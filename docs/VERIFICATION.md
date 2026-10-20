# Verifikasi

Jalankan `scripts/dryrun.sh`. Hasil terakhir di sandbox pengembangan (tanpa Docker daemon, tanpa akses PyPI/npm): **10 langkah lolos, 0 gagal** (31 test Python, 27 test Bun).

## Terbukti di sini (offline)
| Hal | Cara |
|---|---|
| Aturan Auto Review (urutan, default, fallback, dry-run vs enforce, fail-closed saat policy rusak, redaksi rahasia di audit, hot-reload) | 14 unit test + skenario 10 kasus × 2 mode |
| Struktur repo: image terkunci (tanpa `:latest`), hanya Murmur membuka port (127.0.0.1), komputer hanya terjangkau lewat sidecar (jaringan `ops-net`), Hermes tidak memegang token komputer, plugin Auto Review ter-mount ke setiap profil bot, hardening kontainer, bind mount ada, secret wajib diisi, `.env` tidak ikut git | `tests/test_repo.py` + `docker compose config` |
| Seed profil idempoten & tidak menimpa kunci yang ada | test + dry-run |
| Sidecar MCP: tools/list (12 tool, tanpa exec), allowlist domain (termasuk domain mirip/skema `file:`/`javascript:`), header token & bot-id ke komputer, `isError` untuk galat, 401/405/400/202, token MCP terpisah dari token komputer, egress policy dikirim saat start dan diulang berkala, daftar domain kosong = `deny_all` | `tests/mcp.test.ts` + smoke proses terpisah |
| Teach: draft → SKILL.md bernama tool MCP, slug berbahaya ditolak | `tests/teach.test.ts` |

## Belum terbukti — perlu home-lab
1. `scripts/dc build` komputer OpenBot & Chromium jalan; screencast/takeover/request_help nyata.
2. Egress policy benar-benar memblok domain di luar allowlist (uji `navigate` ke domain lain lewat link/redirect).
3. Hermes (a) memuat plugin & profil via `seed.sh` (python di image bernama `python3`?), (b) mengenali `mcp_servers` di config profil dan klien MCP-nya cocok dengan sidecar stateless, (c) nama tool tepat `mcp__ops__*`.
4. Tombol persetujuan Telegram untuk aksi `approve`; perilaku saat tak ada manusia (harus blok).
5. `request_help` sampai ke Buddy/Telegram.
6. Konsumsi RAM/CPU (limit: 3 GB, 2 CPU untuk komputer).
7. HTTPS/OAuth Apps, Tailscale/CGNAT.
8. Digest Murmur: `docker buildx imagetools inspect ghcr.io/getumbrel/murmur:0.6` lalu kunci di `versions.env`.
9. `scripts/fetch-openbot.sh` (butuh internet ke GitHub).
10. Plugin Auto Review benar-benar termuat di profil: `docker compose exec hermes ls /opt/data/profiles/ops-holding/plugins` dan cek `auto-review.jsonl` muncul di folder profil setelah bot memakai tool.
11. User `hermes` ada di image (dipakai `seed.sh`) dan folder profil milik user itu, bukan root.

## Bug yang ditemukan & diperbaiki (review setelah PR dibuka)
| Bug | Dampak | Perbaikan |
|---|---|---|
| Plugin di-mount ke `/opt/data/plugins`, padahal Hermes mencari di `<HERMES_HOME>/plugins` = `profiles/<bot>/plugins` | **Auto Review tidak pernah jalan** untuk Ops Holding & Penyidikan | mount ke setiap profil + test |
| Hermes memegang token komputer & satu jaringan dengan komputer | profil lain yang punya terminal (mis. Xaqu) bisa memanggil `/exec` OpenBot langsung | dua token (MCP ≠ komputer), komputer hanya di `ops-net` |
| Egress policy OpenBot hanya di memori, sidecar mengirim sekali | setelah komputer restart, browser menolak semua koneksi sampai sidecar di-restart | kirim ulang tiap 30 detik |
| `files_write` tanpa `contents` | menulis teks `undefined` ke berkas | validasi |
| `seed.sh` dijalankan dua kali | `docker cp` menyalin ke `/tmp/bots/bots`, config lama yang dipakai; berkas jadi milik root | hapus dulu, jalankan sebagai user `hermes` |
| Teach: `computer_type` + `browser_type` | nama jadi `mcp__ops__mcp__ops__browser_type` | penggantian sekali lewat |
| Redaksi audit | rahasia di dict bersarang (mis. `headers.Authorization`) ikut tercatat | redaksi rekursif |

## Celah yang diketahui (belum diperbaiki, by design Fase 0)
- `money-words` hanya memeriksa teks yang **diketik**; klik tombol "Bayar" (`browser_click` hanya membawa `ref`) tetap `allow`. Penjaga sebenarnya: allowlist domain + manusia memegang login pembayaran (`request_help`).
- Profil tanpa kebijakan memakai `fallback` (default `allow`). Bot baru (Media, Trading, …) **wajib** diberi entri di `policy.yaml` sebelum `enforce`.
- Semua profil berbagi satu container Hermes: `OPS_MCP_TOKEN` terbaca oleh profil yang punya terminal. Dampaknya terbatas pada 12 tool sidecar (dengan allowlist), bukan `/exec`. Isolasi penuh = Hermes terpisah (Fase 2).

## Batasan yang disengaja
Tidak ada LLM-reviewer; Penyidikan hanya terkunci lewat config; sidecar tidak punya tool exec/terminal.
