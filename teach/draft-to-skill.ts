// Teach-mode: draft demonstrasi OpenBot (JSON) -> skill Hermes (SKILL.md).
// Pakai: bun teach/draft-to-skill.ts <draft.json> --server ops --out <folder skills profil>
// Daftar tool yang dibutuhkan dipetakan ke nama MCP Hermes (mcp__<server>__<tool>) agar Auto Review bisa mencocokkan.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";

export type Draft = { slug: string; title: string; summary: string; instructions: string; requiredTools: string[]; sourceRecordingId: string };

const MAP: Record<string, string> = {
  computer_click: "browser_click", computer_type: "browser_type", computer_key: "browser_key",
  computer_scroll: "browser_scroll", computer_request_help: "request_help",
};

export function toSkill(d: Draft, server: string): { slug: string; markdown: string } {
  if (!/^[a-z0-9][a-z0-9-]*$/.test(d.slug)) throw new Error(`slug tidak valid: ${d.slug}`);
  const wire = (t: string) => `mcp__${server}__${MAP[t] ?? t}`;
  const tools = ["browser_snapshot", ...d.requiredTools.map((t) => MAP[t] ?? t)].filter((t, i, a) => a.indexOf(t) === i).map((t) => `mcp__${server}__${t}`);
  const body = d.requiredTools.reduce((s, t) => s.replaceAll(t, wire(t)), d.instructions).replaceAll("browser snapshot", `snapshot (${wire("browser_snapshot")})`);
  const markdown = `---
name: ${d.slug}
description: ${JSON.stringify(d.summary || d.title)}
version: 1.0.0
metadata:
  repos:
    source: openbot-teach:${d.sourceRecordingId}
    requires_tools: [${tools.join(", ")}]
---

# ${d.title}

> Skill ini tidak memberi izin. Alat di bawah tetap lewat Auto Review.
> Alat yang dibutuhkan: ${tools.map((t) => `\`${t}\``).join(", ")}

${body}
`;
  return { slug: d.slug, markdown };
}

if (import.meta.main) {
  const a = process.argv.slice(2);
  const opt = (k: string, dflt?: string) => (a.includes(k) ? a[a.indexOf(k) + 1] : dflt);
  const file = a[0];
  const out = opt("--out");
  if (!file || file.startsWith("--") || !out) throw new Error("pakai: bun teach/draft-to-skill.ts <draft.json> --server ops --out <folder>");
  const { slug, markdown } = toSkill(JSON.parse(readFileSync(file, "utf8")), opt("--server", "ops")!);
  mkdirSync(`${out}/${slug}`, { recursive: true });
  writeFileSync(`${out}/${slug}/SKILL.md`, markdown);
  console.log(`${out}/${slug}/SKILL.md`);
}
