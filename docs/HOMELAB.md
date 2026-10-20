# Menjalankan di home-lab

Prasyarat: Docker + Compose v2, git, ±6 GB RAM kosong untuk pilot (Murmur+Hermes ±1–2 GB, komputer Chromium ≤3 GB), akses internet keluar.

1. `git clone` repo, `git checkout phase0/foundation`.
2. `cp .env.example .env` lalu isi semua nilai (`openssl rand -hex 24`) dan `OPS_ALLOWED_DOMAINS` (pisah koma, mis. `example.com,*.bankanda.co.id`). Isi API key LLM sesuai Hermes.
3. `scripts/fetch-openbot.sh` → `scripts/dc up -d --build` → `scripts/seed.sh`.
4. Buka Murmur di `http://127.0.0.1:3000` (akses jarak jauh: Tailscale/reverse proxy HTTPS; jangan buka port ke internet).
5. Biarkan `mode: dry-run` di `plugins/auto-review/policy.yaml` beberapa hari; baca `profiles/ops-holding/auto-review.jsonl`, rapikan aturan, lalu ubah `mode: enforce` (policy dibaca ulang otomatis; ganti dengan env `AUTOREVIEW_MODE` bila perlu) .
6. Jalankan checklist "perlu home-lab" di `VERIFICATION.md` dan catat hasilnya.

## Mohon dikirim (belum dijawab)
CPU/RAM/disk, OS/hypervisor, ada GPU atau tidak, Tailscale/domain/CGNAT, beban lain di server — untuk menetapkan jumlah bot yang muat dan keputusan Fase 2.
