#!/usr/bin/env python3
"""Validate a Rakazo plugin folder against the rules Rakazo applies on install.

Mirrors elie222/rakazo (docs/build-a-plugin.md, packages/adapters/src/plugin-connectors.ts,
packages/core/src/agent-skill.ts) as of 2026-10:
  - plugin.json: $schema 1.1.0, name 1-64 chars [a-z0-9.-], no '--' or '..'
  - mcp.json: same schema version, only $schema + mcpServers, entries type/url/headers,
    type streamable-http|sse, https URL, no ${VAR} placeholders
  - skills/<name>/SKILL.md: frontmatter with simple 'key: value' lines, name <= 80, description <= 2000
  - companion files: text only (.md .mdx .txt .json .yaml .yml .csv), <= 40 per skill, <= 400,000 bytes per skill
  - commands/<name>.md, agents/<name>.md: agents need name+description frontmatter
  - <= 200 files, <= 100,000 bytes per file, <= 4,000,000 bytes total, no symlinks
Usage: python3 scripts/validate_plugin.py rakazo-plugin
"""

from __future__ import annotations

import json
import os
import re
import sys

PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.1.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.1.0/mcp.schema.json"
NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
TEXT_RE = re.compile(r"\.(md|mdx|txt|json|ya?ml|csv)$", re.I)
FRONT_RE = re.compile(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n?")
KEY_RE = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")


def parse_front(text: str):
    m = FRONT_RE.match(text.lstrip("﻿"))
    if not m:
        return None, "must start with YAML frontmatter (--- ... ---)"
    out = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace():
            return None, f"indented frontmatter line not supported here: {line!r}"
        km = KEY_RE.match(line)
        if not km:
            return None, f"invalid frontmatter line: {line!r}"
        val = km.group(2).strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        out[km.group(1)] = val
    return out, None


def main(root: str) -> int:
    errors, warnings = [], []
    files = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if os.path.islink(p):
                errors.append(f"{rel}: symlinks are not installed")
            files.append((rel, p))
    total = sum(os.path.getsize(p) for _, p in files)
    if len(files) > 200:
        errors.append(f"{len(files)} files (max 200)")
    if total > 4_000_000:
        errors.append(f"{total} bytes total (max 4,000,000)")
    for rel, p in files:
        if os.path.getsize(p) > 100_000:
            errors.append(f"{rel}: {os.path.getsize(p)} bytes (max 100,000)")

    # manifest
    try:
        manifest = json.load(open(os.path.join(root, "plugin.json"), encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"plugin.json: {exc}")
        manifest = {}
    if manifest:
        if manifest.get("$schema") != PLUGIN_SCHEMA:
            errors.append("plugin.json: $schema must be the 1.1.0 plugin schema")
        name = manifest.get("name", "")
        if not (1 <= len(name) <= 64 and NAME_RE.match(name)):
            errors.append(f"plugin.json: invalid name {name!r}")

    # mcp
    mcp_path = os.path.join(root, "mcp.json")
    if os.path.exists(mcp_path):
        raw = open(mcp_path, encoding="utf-8").read()
        if "${" in raw:
            errors.append("mcp.json: ${VAR} placeholders are rejected")
        doc = json.loads(raw)
        if doc.get("$schema") != MCP_SCHEMA:
            errors.append("mcp.json: $schema must match the plugin schema version")
        if set(doc) - {"$schema", "mcpServers"}:
            errors.append("mcp.json: only $schema and mcpServers allowed")
        for sname, s in (doc.get("mcpServers") or {}).items():
            if set(s) - {"type", "url", "headers"}:
                errors.append(f"mcp.json/{sname}: only type, url, headers allowed")
            if s.get("type") not in ("streamable-http", "sse"):
                errors.append(f"mcp.json/{sname}: type must be streamable-http or sse")
            if not str(s.get("url", "")).startswith("https://"):
                errors.append(f"mcp.json/{sname}: url must be https")

    # skills
    skill_names = set()
    skills_dir = os.path.join(root, "skills")
    for skill in sorted(os.listdir(skills_dir)) if os.path.isdir(skills_dir) else []:
        sdir = os.path.join(skills_dir, skill)
        smd = os.path.join(sdir, "SKILL.md")
        if not os.path.exists(smd):
            errors.append(f"skills/{skill}: missing SKILL.md")
            continue
        front, err = parse_front(open(smd, encoding="utf-8").read())
        if err:
            errors.append(f"skills/{skill}/SKILL.md: {err}")
            continue
        n, d = front.get("name", ""), front.get("description", "")
        if not n or not d:
            errors.append(f"skills/{skill}/SKILL.md: name and description required")
        if len(n) > 80 or len(d) > 2000:
            errors.append(f"skills/{skill}/SKILL.md: name <= 80 and description <= 2000 chars")
        if n.lower() in skill_names:
            errors.append(f"duplicate skill name {n}")
        skill_names.add(n.lower())
        companions = [(r, p) for r, p in files if r.startswith(f"skills/{skill}/") and r != f"skills/{skill}/SKILL.md"]
        nontext = [r for r, _ in companions if not TEXT_RE.search(r)]
        if nontext:
            warnings.append(f"skills/{skill}: non-text companions are skipped: {nontext}")
        if len(companions) > 40:
            errors.append(f"skills/{skill}: {len(companions)} companion files (max 40)")
        size = sum(os.path.getsize(p) for _, p in companions) + os.path.getsize(smd)
        if size > 400_000:
            errors.append(f"skills/{skill}: {size} bytes (max 400,000)")
        for ref in re.findall(r"\]\((references/[^)]+)\)", open(smd, encoding="utf-8").read()):
            if not os.path.exists(os.path.join(sdir, ref)):
                errors.append(f"skills/{skill}/SKILL.md links missing {ref}")

    for kind in ("agents", "commands"):
        d = os.path.join(root, kind)
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if not f.endswith(".md"):
                continue
            text = open(os.path.join(d, f), encoding="utf-8").read()
            front, err = parse_front(text)
            if kind == "agents":
                if err or not front.get("name") or not front.get("description"):
                    errors.append(f"agents/{f}: needs name and description frontmatter ({err or 'missing'})")
                elif front["name"].lower() in skill_names:
                    errors.append(f"agents/{f}: name collides with a skill")
                else:
                    skill_names.add(front["name"].lower())
            else:
                cname = f[:-3]
                if cname.startswith("_"):
                    continue
                if cname.lower() in skill_names:
                    warnings.append(f"commands/{f}: same name as a skill; Rakazo skips it")
                if err:
                    warnings.append(f"commands/{f}: no valid frontmatter; first line becomes the description")

    print(f"{root}: {len(files)} files, {total} bytes, {len(skill_names)} skills/agents")
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "rakazo-plugin"))
