# Uji coba ponytail (2026-10-20)

Plugin `ponytail@ponytail` 5.3.2 (DietrichGebert/ponytail) dipasang lewat `claude plugin install`, lalu dijalankan headless
dengan izin baca saja: `/ponytail:ponytail-audit` (seluruh repo) → perbaikan → `/ponytail:ponytail-review` (diff perbaikan).
Beban yang diasumsikan: satu pemilik, 1–2 bot, satu VM Proxmox 6 GB.

## Putaran 0: aturan ponytail diterapkan manual (sebelum plugin terpasang)
| # | Temuan | Status |
|---|---|---|
| a | Verifier LLM menilai `files_write` tanpa melihat isi | diperbaiki + tes |
| b | `eval/rakazo/run.sh up` jalan tanpa aturan iptables (LAN/Proxmox :8006 terjangkau) | diperbaiki |
| c | `llm: true` diabaikan pada aturan tanpa `id` | diperbaiki + tes |

## Putaran 1: `/ponytail:ponytail-audit`
| # | Tingkat | Temuan | Status |
|---|---|---|---|
| 1 | Must | Skrip root Rakazo diunduh dari `main` | dipin ke commit 08ee8cf |
| 2 | Must | Profil tak dikenal → `fallback: allow` | `fallback: approve` + tes |
| 3 | Should | Murmur boleh tanpa password (dokumen Murmur: kosong = tanpa login) | wajib di compose + tes |
| 4 | Should | Panggilan ke komputer tanpa timeout | `CALL_TIMEOUT_MS` 60 dtk |
| 5 | Should | `restart: on-failure`, tanpa healthcheck → mati setelah reboot VM | `unless-stopped` + healthcheck `ops-mcp`, Hermes menunggu sehat |
| 6 | Should | Gagal tulis audit log diam saja (log kosong terbaca "bersih") | ditulis ke stderr |
| 7 | Should | Seed ulang menimpa list → toolset yang dimatikan manual hidup lagi | list digabung + tes |
| 8 | Should | `dryrun.sh` mengulang tes | **ditolak**: dry-run adalah laporan skenario untuk pemilik, sengaja dipertahankan |
| 9 | Nice | `unittest.main()` di tengah berkas | dipindah ke akhir |
| 10 | Nice | Dokumen tidak sesuai kode (LLM reviewer, limit RAM, 8 vs 6 GB) | diperbarui |
| 11 | Nice | Teach: `sourceRecordingId`/tools bisa menyisipkan kunci front matter | di-quote + tes |

## Putaran 2: `/ponytail:ponytail-review` atas perbaikan
Must fix: tidak ada. Diperbaiki: healthcheck pakai `127.0.0.1` + `start_period` (risiko IPv6 `::1`); error timeout
menyebut path dan memperingatkan agar tidak mengulang aksi membabi buta; catatan bahwa list seed hanya bertambah;
catatan wajib `MURMUR_PASSWORD`.

Bug yang tertangkap saat memverifikasi putaran 2: komentar sebaris `MURMUR_PASSWORD=  # ...` dibaca Compose sebagai
**isi password**. Komentar dipindah ke baris sendiri, dan ada tes yang melarang komentar sebaris di `.env.example`.

## Belum diuji
Runtime (Docker image, Chromium, Hermes, panggilan LLM nyata). Docker daemon jalan di sandbox, tetapi kebijakan jaringan
menolak `registry-1.docker.io` dan `ghcr.io` (403), jadi image tidak bisa ditarik. Uji runtime di VM Proxmox: `docs/HOMELAB.md`.
