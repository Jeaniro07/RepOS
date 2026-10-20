# Verifikasi

Jalankan `scripts/dryrun.sh`. Hasil terakhir: **10 langkah lolos, 0 gagal** (45 test Python, 28 test Bun).

## Terbukti di sini (offline)
| Hal | Cara |
|---|---|
| Aturan Auto Review (urutan, default, fallback, dry-run vs enforce, fail-closed saat policy rusak, redaksi rahasia di audit, hot-reload) | 14 unit test + skenario 10 kasus × 2 mode |
| Struktur repo: image terkunci (tanpa `:latest`), hanya Murmur membuka port (127.0.0.1), komputer hanya terjangkau lewat sidecar (jaringan `ops-net`), Hermes tidak memegang token komputer, plugin Auto Review ter-mount ke setiap profil bot, hardening kontainer, bind mount ada, secret wajib diisi, `.env` tidak ikut git | `tests/test_repo.py` + `docker compose config` |
| Seed profil idempoten & tidak menimpa kunci yang ada | test + dry-run |
| Sidecar MCP: tools/list (12 tool, tanpa exec), allowlist domain (termasuk domain mirip/skema `file:`/`javascript:`), header token & bot-id ke komputer, `isError` untuk galat, 401/405/400/202, token MCP terpisah dari token komputer, egress policy dikirim saat start dan diulang berkala, daftar domain kosong = `deny_all` | `tests/mcp.test.ts` + smoke proses terpisah |
| Teach: draft → SKILL.md bernama tool MCP, slug berbahaya ditolak | `tests/teach.test.ts` |

## Terbukti dengan komponen asli di sandbox (2026-10-20, tanpa image Docker)
Registry Docker diblokir di sandbox, jadi komponen dijalankan dari source pada commit yang dipin:
OpenBot agent-computer `e8bb273` + Chromium (headed, X), sidecar RepOS, Hermes `0b10b9f` (pemuat plugin saja).
| Uji | Hasil |
|---|---|
| Sidecar ↔ OpenBot asli: header token/bot-id, 12 tool, `files_write`/`files_read`, `..` ditolak, screenshot PNG | lolos |
| Token salah / token komputer ke sidecar → 401; token MCP ke `/exec` komputer → "Not authorised." | lolos |
| Egress: domain di allowlist diteruskan ke hulu; domain lain ditolak di CONNECT **walau sidecar dilewati**; `169.254.169.254` ditolak ("cloud metadata … no Bot may reach") | lolos |
| Komputer di-restart → sidecar mengirim ulang policy (bug #3 lama) | lolos |
| Pemuat plugin Hermes memuat Auto Review per profil; `terminal`→block, teks bayar→approve `rule_key=money-words`, klik→allow, `files_write`→approve, tak dikenal→approve; audit log tertulis | lolos **setelah perbaikan**: Hermes baru tidak membawa PyYAML, plugin gagal import dan bot jalan tanpa penjaga. Kini memakai `hermes_yaml` bila ada |
| Kontrak hook di source Hermes: `block` (wajib pesan) > `approve` (+`rule_key`); approval gagal/timeout → block; batas hook 30 dtk, timeout → block | sesuai plugin |

Batas uji ini: Playwright 1.56 (image memakai 1.62.1) dengan shim satu baris untuk snapshot, halaman web nyata
tidak terbuka karena proxy sandbox, Hermes gateway/Telegram/LLM tidak dijalankan.

## Belum terbukti — perlu home-lab
1. `scripts/dc build` komputer OpenBot & Chromium jalan; screencast/takeover/request_help nyata.
2. Egress policy benar-benar memblok domain di luar allowlist (uji `navigate` ke domain lain lewat link/redirect).
3. Hermes (a) memuat plugin & profil via `seed.sh` (python di image bernama `python3`?), (b) mengenali `mcp_servers` di config profil dan klien MCP-nya cocok dengan sidecar stateless, (c) nama tool tepat `mcp__ops__*`.
4. Tombol persetujuan Telegram untuk aksi `approve`; perilaku saat tak ada manusia (harus blok).
5. `request_help` sampai ke Buddy/Telegram.
6. Konsumsi RAM/CPU (limit komputer: 2 GB, 1,5 CPU; total ±4,1 GB di VM 6 GB).
7. HTTPS/OAuth Apps, Tailscale/CGNAT.
8. Digest Murmur: `docker buildx imagetools inspect ghcr.io/getumbrel/murmur:0.6` lalu kunci di `versions.env`.
9. `scripts/fetch-openbot.sh` (butuh internet ke GitHub).
10. Plugin Auto Review benar-benar termuat di image v0.22.0: di Murmur minta Ops Holding menjalankan `ls` di terminal → harus dijawab `BLOCKED [auto-review:no-exec]`, dan `auto-review.jsonl` muncul di folder profil. Jika tool jalan, plugin tidak termuat: **jangan dipakai**.
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
- Profil tanpa kebijakan memakai `fallback` (default `approve`). Bot baru (Media, Trading, …) tetap perlu entri sendiri di `policy.yaml` agar tidak semua aksi minta persetujuan.
- Plugin yang gagal dimuat tidak memblok apa pun (Hermes melewatinya). Karena itu uji no. 10 wajib setiap ganti versi Hermes.
- Semua profil berbagi satu container Hermes: `OPS_MCP_TOKEN` terbaca oleh profil yang punya terminal. Dampaknya terbatas pada 12 tool sidecar (dengan allowlist), bukan `/exec`. Isolasi penuh = Hermes terpisah (Fase 2).

## Batasan yang disengaja
Verifier LLM opsional dan terbatas (lihat `MERGED.md`); Penyidikan hanya terkunci lewat config; sidecar tidak punya tool exec/terminal.
