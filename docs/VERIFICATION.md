# Verifikasi

Jalankan `scripts/dryrun.sh`. Hasil terakhir di sandbox pengembangan (tanpa Docker daemon, tanpa akses PyPI/npm): **9 langkah lolos, 0 gagal**.

## Terbukti di sini (offline)
| Hal | Cara |
|---|---|
| Aturan Auto Review (urutan, default, fallback, dry-run vs enforce, fail-closed saat policy rusak, redaksi rahasia di audit, hot-reload) | 14 unit test + skenario 10 kasus × 2 mode |
| Struktur repo: image terkunci (tanpa `:latest`), hanya Murmur membuka port (127.0.0.1), komputer hanya di jaringan `bots`, hardening kontainer, bind mount ada, token konsisten, secret wajib diisi, `.env` tidak ikut git | `tests/test_repo.py` + `docker compose config` |
| Seed profil idempoten & tidak menimpa kunci yang ada | test + dry-run |
| Sidecar MCP: tools/list (12 tool, tanpa exec), allowlist domain (termasuk domain mirip/skema `file:`/`javascript:`), header token & bot-id ke komputer, `isError` untuk galat, 401/405/400/202, egress policy dikirim saat start | `tests/mcp.test.ts` (21 test Bun total) + smoke proses terpisah |
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

## Batasan yang disengaja
Tidak ada LLM-reviewer; Penyidikan hanya terkunci lewat config; sidecar tidak punya tool exec/terminal.
