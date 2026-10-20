"""Auto Review: hook pre_tool_call per profil. Hanya stdlib + PyYAML (sudah ada di Hermes).

Urutan: aturan pertama yang cocok menang (deny | allow | approve), lalu `default`.
Gagal evaluasi di mode enforce -> blok (fail-closed). dry-run tidak pernah memblok, hanya mencatat.
"""
import fnmatch
import json
import os
import re
import time
from pathlib import Path

import yaml

HERE = Path(__file__).parent
SECRET_KEYS = {"text", "contents", "password", "token", "secret", "authorization", "api_key"}
_cache = {"mtime": None, "path": None, "data": {}}


def profile_name():
    """Nama profil dari HERMES_HOME aktif (ContextVar di gateway, env di CLI)."""
    try:
        from hermes_constants import get_hermes_home
        home = Path(get_hermes_home())
    except Exception:
        home = Path(os.environ.get("HERMES_HOME", ""))
    return home.name if home.parent.name == "profiles" else "default"


def load_policy():
    path = Path(os.environ.get("AUTOREVIEW_POLICY") or HERE / "policy.yaml")
    mtime = path.stat().st_mtime
    if (_cache["path"], _cache["mtime"]) != (path, mtime):  # hot-reload saat berkas berubah
        _cache.update(path=path, mtime=mtime, data=yaml.safe_load(path.read_text()) or {})
    return _cache["data"]


def decide(policy, profile, tool, args):
    """-> (action, rule_id, reason). action: allow | deny | approve."""
    prof = (policy.get("profiles") or {}).get(profile) or policy.get("fallback") or {}
    for i, rule in enumerate(prof.get("rules") or []):
        if not fnmatch.fnmatchcase(tool, rule["tool"]):
            continue
        if any(not re.search(rx, str(args.get(k, ""))) for k, rx in (rule.get("args") or {}).items()):
            continue
        return rule["action"], rule.get("id", f"rule{i}"), rule.get("reason", "")
    return prof.get("default", "approve"), "default", "tidak ada aturan yang cocok"


def redact(args):
    return {k: ("<disembunyikan>" if k.lower() in SECRET_KEYS else str(v)[:80]) for k, v in (args or {}).items()}


def audit(entry):
    try:
        try:
            from hermes_constants import get_hermes_home
            home = Path(get_hermes_home())
        except Exception:
            home = Path(os.environ.get("HERMES_HOME", "."))
        with (home / "auto-review.jsonl").open("a") as f:
            f.write(json.dumps({"ts": int(time.time()), **entry}, ensure_ascii=False) + "\n")
    except Exception:
        pass  # audit tidak boleh menjatuhkan agent


def review(tool_name, args=None, **_):
    args = args if isinstance(args, dict) else {}
    policy, profile = {}, "?"
    mode = os.environ.get("AUTOREVIEW_MODE", "enforce")
    try:
        policy = load_policy()
        mode = os.environ.get("AUTOREVIEW_MODE") or policy.get("mode", "enforce")
        profile = profile_name()
        action, rule, reason = decide(policy, profile, tool_name, args)
    except Exception as e:  # fail-closed
        action, rule, reason = "deny", "error", f"auto-review error: {type(e).__name__}"
    audit({"profile": profile, "tool": tool_name, "action": action, "rule": rule, "mode": mode, "args": redact(args)})
    if mode != "enforce" or action == "allow":
        return None
    msg = f"[auto-review:{rule}] {reason or action}"
    if action == "approve":
        return {"action": "approve", "message": f"{tool_name}: {reason or 'butuh persetujuan'}", "rule_key": rule}
    return {"action": "block", "message": f"BLOCKED {msg}"}


def register(ctx):
    ctx.register_hook("pre_tool_call", review)
