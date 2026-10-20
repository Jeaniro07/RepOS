#!/usr/bin/env bash
# Uji di VM Proxmox (setelah `scripts/dc up -d --build` + `scripts/seed.sh`). Satu perintah, hasilnya ditempel ke PR/chat:
#   scripts/homelab-check.sh 2>&1 | tee homelab-check.txt
set -uo pipefail
cd "$(dirname "$0")/.."
pass=0; fail=0
step() { printf '\n== %s\n' "$1"; }
ok()   { printf '   OK    %s\n' "$1"; pass=$((pass+1)); }
bad()  { printf '   GAGAL %s\n' "$1"; fail=$((fail+1)); }
check() { local name=$1; shift; if out=$("$@" 2>&1); then ok "$name"; else bad "$name"; fi; printf '%s\n' "$out" | tail -8 | sed 's/^/         /'; }
envval() { sed -n "s/^$1=//p" .env | tail -1; }

step "1. VM (target: 4 vCPU, RAM 6 GB tanpa balloon, swap 4 GB)"
echo "   CPU $(nproc) | $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2)"
free -m | sed 's/^/   /'
check "virtualisasi KVM (bukan LXC)" sh -c '[ "$(systemd-detect-virt 2>/dev/null)" = kvm ]'
check "swap aktif" sh -c '[ "$(awk "/SwapTotal/{print \$2}" /proc/meminfo)" -gt 0 ]'

step "2. Tailscale (di dalam VM, serve ke :3000, tanpa funnel)"
check "tailscale terhubung" tailscale status --self --peers=false
check "serve meneruskan ke 127.0.0.1:3000" sh -c 'tailscale serve status | grep -q "127.0.0.1:3000"'
check "funnel MATI (tidak terbuka ke internet)" sh -c '! tailscale funnel status 2>/dev/null | grep -qi "funnel on"'
check "Murmur hanya di 127.0.0.1:3000" sh -c 'ss -ltn | grep ":3000 " | grep -q "127.0.0.1:3000" && ! ss -ltn | grep ":3000 " | grep -vq "127.0.0.1:3000"'
TSURL=$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null)
[ -n "$TSURL" ] && check "Murmur terjangkau via https://$TSURL" curl -fsS -o /dev/null --max-time 10 "https://$TSURL/"

step "3. Kontainer (semua jalan, ops-mcp sehat, restart unless-stopped)"
scripts/dc ps --format 'table {{.Service}}\t{{.State}}\t{{.Status}}' | sed 's/^/   /'
for s in murmur hermes ops-computer ops-mcp; do
  check "$s jalan" sh -c "scripts/dc ps --status running --services | grep -qx $s"
done
check "ops-mcp healthy" sh -c 'scripts/dc ps ops-mcp | grep -q healthy'

step "4. Auto Review termuat di Hermes asli dan memblok terminal"
PY=$(scripts/dc exec -T hermes sh -c 'head -1 "$(command -v hermes)" | sed "s/^#!//"' 2>/dev/null)
case "$PY" in /*python*) ;; *) PY=python3 ;; esac
check "terminal -> block (mode enforce)" scripts/dc exec -T -u hermes -e AUTOREVIEW_MODE=enforce \
  -e HERMES_HOME=/opt/data/profiles/ops-holding hermes $PY -c '
import importlib.util as u
s = u.spec_from_file_location("ar", "/opt/data/profiles/ops-holding/plugins/auto-review/__init__.py")
m = u.module_from_spec(s); s.loader.exec_module(m)
r = m.review("terminal", {"command": "ls"}); print(r); assert r and r["action"] == "block"'
check "audit log tertulis" scripts/dc exec -T hermes test -s /opt/data/profiles/ops-holding/auto-review.jsonl
echo "   Mode policy saat ini: $(grep -m1 '^mode:' plugins/auto-review/policy.yaml)"
echo "   MANUAL: di Murmur minta Ops Holding menjalankan 'ls' -> harus BLOCKED [auto-review:no-exec] (setelah mode: enforce)."

step "5. Komputer bot: sidecar + egress (melewati sidecar langsung ke OpenBot)"
ALLOWED=$(envval OPS_ALLOWED_DOMAINS); FIRST=${ALLOWED%%,*}; FIRST=${FIRST#\*.}
MCP=$(envval OPS_MCP_TOKEN)
# Dari dalam kontainer sidecar, langsung ke API komputer dengan token komputer: sidecar dilewati, yang menjaga hanya egress.
nav() { scripts/dc exec -T ops-mcp bun -e '
const r = await fetch(process.env.COMPUTER_URL + "/navigate", { method: "POST",
  headers: { "x-openbot-computer-token": process.env.COMPUTER_TOKEN, "x-openbot-bot-id": process.env.BOT_ID, "content-type": "application/json" },
  body: JSON.stringify({ url: process.argv[1] }) });
console.log(r.status, (await r.text()).slice(0, 300));' "$1"; }
mcp() { scripts/dc exec -T ops-mcp bun -e '
const r = await fetch("http://127.0.0.1:8700/mcp", { method: "POST",
  headers: { authorization: "Bearer " + process.argv[1], "content-type": "application/json" },
  body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list" }) });
console.log(r.status, r.ok ? (await r.json()).result.tools.length + " tool" : "");' "$1"; }
# Bentuk respons OpenBot asli (diuji di sandbox): blok egress -> HTTP 502 "goto: net::ERR_..."; 200 bisa berisi halaman tolak.
opens()  { local o; o=$(nav "$1"); echo "$o"; [[ $o == 200* && $o != *"request blocked"* ]]; }
blocked() { local o; o=$(nav "$1"); echo "$o"; [[ $o != 200* || $o != *"$2"* ]]; }
check "sidecar menolak token salah (401)" eval '[[ $(mcp salah) == 401* ]]'
check "sidecar: 12 tool dengan token MCP" eval '[[ $(mcp "$MCP") == "200 12 tool" ]]'
[ -n "$FIRST" ] && check "domain diizinkan terbuka: $FIRST" opens "https://$FIRST/"
case ",$ALLOWED," in
  *,example.org,*) echo "   (lewati uji blok: example.org ada di allowlist)" ;;
  *) check "domain lain DIBLOK walau sidecar dilewati (example.org)" blocked https://example.org/ "Example Domain" ;;
esac
check "metadata cloud 169.254.169.254 DIBLOK" eval '[[ $(nav http://169.254.169.254/) != 200* ]]'
check "komputer tidak punya port di host" sh -c '! scripts/dc port ops-computer 4100 2>/dev/null | grep -q .'

step "6. Pemakaian sumber daya (anggaran ±4,1 GB)"
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}' | sed 's/^/   /'

printf '\n== Ringkasan: %d lolos, %d gagal\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
