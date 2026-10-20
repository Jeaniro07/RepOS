#!/usr/bin/env bash
# Uji Rakazo berdampingan dengan RepOS. Tidak menyentuh stack RepOS (nama proyek compose terpisah).
#   eval/rakazo/run.sh prepare   unduh compose + buat .env acak (belum jalan)
#   eval/rakazo/run.sh egress    pasang aturan egress host (butuh sudo, Linux iptables)
#   eval/rakazo/run.sh up        pull + jalankan, catat digest image ke work/DIGESTS.txt
#   eval/rakazo/run.sh down      hentikan (data tetap); `down -v` hapus data
set -Eeuo pipefail
cd "$(dirname "$0")"
W=work; BASE="${RAKAZO_DOWNLOAD_BASE:-https://raw.githubusercontent.com/elie222/rakazo/main/infra/compose}"
export COMPOSE_PROJECT_NAME=rakazo-eval
mkdir -p "$W"; cd "$W"
dc() { docker compose --env-file .env -f docker-compose.images.yml "$@"; }

case "${1:-}" in
  prepare)
    for f in install-images.sh restrict-computer-egress.sh; do curl -fsSL "$BASE/$f" -o "$f"; done
    RAKAZO_DOWNLOAD_BASE="$BASE" bash install-images.sh --prepare-only
    # tambahkan override sekali saja (nilai terakhir menang di .env)
    grep -q '^# --- RepOS eval' .env || { printf '\n# --- RepOS eval\n' >> .env; grep -v '^\s*#' ../overrides.env | grep . >> .env; }
    echo "Siap. Isi kunci model di $PWD/.env, lalu: run.sh egress && run.sh up" ;;
  egress) sudo bash restrict-computer-egress.sh ;;
  up)
    grep -q '^SANDBOX_COMPUTER_EGRESS=restricted' .env || { echo "egress belum restricted" >&2; exit 1; }
    # Tanpa aturan iptables, komputer bot bisa menjangkau LAN (mis. UI Proxmox :8006).
    sudo iptables -S DOCKER-USER 2>/dev/null | grep -q rakazo-c || { echo "aturan egress belum terpasang: jalankan run.sh egress" >&2; exit 1; }
    dc pull && dc up -d --wait --wait-timeout 300
    { date -u +%FT%TZ; dc config --images | sort -u | xargs -I{} docker image inspect {} --format '{{index .RepoDigests 0}}'; } > DIGESTS.txt
    echo "UI: http://127.0.0.1:5173 — digest tercatat di $PWD/DIGESTS.txt (pin ke sini untuk uji ulang)" ;;
  down) shift; dc down "$@" ;;
  *) sed -n 2,7p "$0"; exit 2 ;;
esac
