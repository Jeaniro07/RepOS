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

## Putaran 3: uji runtime komponen asli + `/ponytail:ponytail-review` kedua
Image tidak bisa ditarik (registry diblokir di sandbox), jadi OpenBot agent-computer, sidecar, dan pemuat plugin Hermes
dijalankan dari source yang dipin (hasil: `VERIFICATION.md`). Bug yang hanya muncul di runtime:
| # | Tingkat | Temuan | Status |
|---|---|---|---|
| 1 | Must | Hermes baru tidak membawa PyYAML → plugin Auto Review gagal import, Hermes melewatinya, **bot jalan tanpa penjaga** | `hermes_yaml` dengan fallback PyYAML + tes |
| 2 | Must | `seed.py` punya bug yang sama | idem, dijalankan dengan Python milik Hermes + tes |
| 3 | Should | Tidak ada bukti plugin termuat setelah seed | `seed.sh` memuat plugin dan gagal keras bila tidak bisa; uji `ls` → `BLOCKED` di HOMELAB langkah 5 |
| 4 | Should | `bun test` ikut menjalankan ribuan tes vendor OpenBot | `bunfig.toml` (`root = "./tests"`) |
| 5 | Nice | Tes mengubah `sys.modules` manual | `mock.patch.dict` |

## Belum diuji
Stack penuh dari image, Chromium versi image, Hermes gateway + Telegram + LLM nyata, Proxmox/Tailscale.
Uji ini di VM Proxmox: `docs/HOMELAB.md` langkah 1–5, lalu `VERIFICATION.md` "perlu home-lab".
