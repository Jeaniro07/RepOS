#!/usr/bin/env bash
# Dry-run Fase 0 tanpa Docker daemon / internet: semua yang bisa dibuktikan statis atau lewat proses lokal.
# Yang BUTUH Docker/Chromium/Telegram ada di docs/VERIFICATION.md (uji di home-lab).
set -uo pipefail
cd "$(dirname "$0")/.."
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass=0; fail=0
step() { printf '\n== %s\n' "$1"; }
ok()   { printf '   OK   %s\n' "$1"; pass=$((pass+1)); }
bad()  { printf '   GAGAL %s\n' "$1"; fail=$((fail+1)); }
run()  { local name=$1; shift; if out=$("$@" 2>&1); then ok "$name"; else bad "$name"; printf '%s\n' "$out" | tail -15; fi; }

step "1. Unit test Python (plugin Auto Review, struktur repo, seed)"
run "python unittest" python3 -I -m unittest discover -s tests -p 'test_*.py'

step "2. Test Bun (sidecar MCP vs agent-computer palsu, teach)"
run "bun test" bun test

step "3. Validasi compose (env dummy, tanpa daemon)"
cat > "$T/e.env" <<E
MURMUR_HERMES_PASSWORD=x
MURMUR_HERMES_SECRET=x
MURMUR_PASSWORD=x
OPS_TOKEN=x
OPS_ALLOWED_DOMAINS=example.com
E
run "docker compose config" env ENV_FILE="$T/e.env" scripts/dc config -q

step "4. Auto Review: skenario nyata dengan policy.yaml asli"
cat > "$T/scenario.py" <<'PY'
import importlib.util, json, os, sys
from pathlib import Path
root, tmp = Path(sys.argv[1]), Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("ar", root / "plugins/auto-review/__init__.py")
ar = importlib.util.module_from_spec(spec); spec.loader.exec_module(ar)

CASES = [  # profil, tool, args, keputusan yang diharapkan
 ("ops-holding", "mcp__ops__browser_navigate", {"url": "https://example.com"}, "allow"),
 ("ops-holding", "mcp__ops__browser_click", {"ref": "e1"}, "allow"),
 ("ops-holding", "mcp__ops__browser_type", {"ref": "e2", "text": "Klik BAYAR sekarang"}, "approve"),
 ("ops-holding", "mcp__ops__files_write", {"path": "a.txt", "contents": "x"}, "approve"),
 ("ops-holding", "terminal", {"command": "rm -rf /"}, "deny"),
 ("ops-holding", "execute_code", {"code": "print(1)"}, "deny"),
 ("ops-holding", "send_message", {"to": "x"}, "approve"),
 ("penyidikan", "mcp__ops__browser_navigate", {"url": "https://example.com"}, "deny"),
 ("penyidikan", "terminal", {"command": "ls"}, "deny"),
 ("penyidikan", "memory_add", {"text": "catatan"}, "allow"),
]
fails = 0
for mode in ("dry-run", "enforce"):
    os.environ["AUTOREVIEW_MODE"] = mode
    print(f"   -- mode {mode}")
    for prof, tool, args, want in CASES:
        home = tmp / mode / "profiles" / prof; home.mkdir(parents=True, exist_ok=True)
        os.environ["HERMES_HOME"] = str(home)
        res = ar.review(tool, args)
        got = ("deny" if res and res.get("action") == "block" else "approve" if res else "allow")
        expected = "allow" if mode == "dry-run" else want
        status = "ok" if got == expected else "SALAH"
        if status != "ok": fails += 1
        print(f"   {status:5} {prof:12} {tool:30} -> {got:7} (kebijakan: {want})")
    # audit dry-run harus tetap mencatat keputusan kebijakan
    for prof in {c[0] for c in CASES}:
        log = tmp / mode / "profiles" / prof / "auto-review.jsonl"
        n = len(log.read_text().splitlines()) if log.exists() else 0
        want_n = sum(1 for c in CASES if c[0] == prof)
        if n != want_n: fails += 1; print(f"   SALAH audit {mode}/{prof}: {n} baris, harus {want_n}")
# rahasia tidak boleh bocor ke audit
home = tmp / "enforce" / "profiles" / "ops-holding"; os.environ["HERMES_HOME"] = str(home)
ar.review("mcp__ops__browser_type", {"ref": "e", "text": "SANDI-RAHASIA-123", "password": "SANDI-RAHASIA-123"})
leak = "SANDI-RAHASIA-123" in (home / "auto-review.jsonl").read_text()
print("   " + ("SALAH" if leak else "ok   ") + " audit tidak memuat teks rahasia"); fails += leak
sys.exit(1 if fails else 0)
PY
if out=$(python3 -I "$T/scenario.py" "$PWD" "$T/ar" 2>&1); then ok "skenario Auto Review"; else bad "skenario Auto Review"; fi
printf '%s\n' "$out"

step "5. Seed profil bot ke home Hermes sementara (dua kali = idempoten)"
python3 -I hermes/seed.py bots "$T/home" >/dev/null && cp "$T/home/profiles/ops-holding/config.yaml" "$T/first.yaml"
python3 -I hermes/seed.py bots "$T/home" >/dev/null
if cmp -s "$T/first.yaml" "$T/home/profiles/ops-holding/config.yaml" && [ -f "$T/home/profiles/penyidikan/SOUL.md" ]; then ok "seed idempoten, SOUL.md tersalin"; else bad "seed"; fi

step "6. Teach: draft demonstrasi -> SKILL.md"
if bun teach/draft-to-skill.ts tests/fixtures/draft.json --server ops --out "$T/skills" >/dev/null \
   && grep -q 'mcp__ops__' "$T"/skills/*/SKILL.md; then ok "draft -> SKILL.md"; else bad "teach"; fi

step "7. Sidecar MCP sebagai proses terpisah (smoke)"
PORT=$((20000 + RANDOM % 5000))
COMPUTER_URL=http://127.0.0.1:1 COMPUTER_TOKEN=t BOT_ID=ops-holding ALLOWED_DOMAINS=example.com PORT=$PORT bun computer-mcp/server.ts >"$T/mcp.log" 2>&1 &
PID=$!; for _ in $(seq 50); do curl -fs "localhost:$PORT/health" >/dev/null 2>&1 && break; sleep 0.1; done
code_noauth=$(curl -s -o /dev/null -w '%{http_code}' -X POST "localhost:$PORT/mcp" -d '{}')
tools=$(curl -s -X POST "localhost:$PORT/mcp" -H 'authorization: Bearer t' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 -c 'import json,sys;print(len(json.load(sys.stdin)["result"]["tools"]))')
blocked=$(curl -s -X POST "localhost:$PORT/mcp" -H 'authorization: Bearer t' -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"browser_navigate","arguments":{"url":"https://evil.io"}}}')
kill $PID 2>/dev/null
[ "$code_noauth" = 401 ] && ok "tanpa token -> 401" || bad "tanpa token -> $code_noauth"
[ "${tools:-0}" -ge 10 ] && ok "tools/list memuat $tools tool" || bad "tools/list"
grep -q 'tidak diizinkan' <<<"$blocked" && ok "navigate ke evil.io diblok" || bad "navigate diblok"

printf '\n== Ringkasan: %d lolos, %d gagal\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
