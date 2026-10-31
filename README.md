# RepOS

Repo ini berisi dua bagian yang berdiri sendiri:

| Bagian | Untuk apa | Mulai dari |
|---|---|---|
| [Bot self-hosted (Fase 0)](#bot-self-hosted-fase-0) | Bot yang selalu hidup: Hermes + komputer per bot, UI lewat Murmur | `compose.yaml`, `docs/HOMELAB.md` |
| [Sutradara Video Anti-Slop untuk Rakazo](#sutradara-video-anti-slop-untuk-rakazo) | Agent pembuat dan pemeriksa video tanpa AI slop, generasi lewat fal.ai | `rakazo-plugin/`, `install.sh`, `install.ps1` |

## Bot self-hosted (Fase 0)

Bot self-hosted yang selalu hidup: **satu Hermes (profil per bot) + satu komputer (container) per bot**, UI lewat Murmur.
Fase 0 = fondasi + pilot **Ops Holding**. Penyidikan hanya disiapkan sebagai profil terkunci (tanpa browser/internet/konektor).

```
Murmur ──► Hermes (profil: ops-holding, penyidikan, …)
              │  plugin auto-review (pre_tool_call: deny / allow / approve, audit JSONL)
              ▼
         ops-mcp (sidecar MCP, 1 file Bun) ──► ops-computer (OpenBot agent-computer: Chromium + CDP screencast, egress allowlist)
        jaringan "bots", token MCP            jaringan "ops-net", token komputer (Hermes tidak memegangnya)
```

| Bagian | Berkas | Bahasa |
|---|---|---|
| Orkestrasi | `compose.yaml`, `versions.env`, `scripts/dc` | YAML |
| Profil bot | `bots/<bot>/config.yaml`, `SOUL.md`, `hermes/seed.py` | YAML + Python (stdlib+PyYAML) |
| Auto Review | `plugins/auto-review/` (`policy.yaml` = aturan) | Python |
| Komputer per bot | `computer-mcp/server.ts` (tanpa dependensi) | Bun/TS |
| Teach-mode | `teach/draft-to-skill.ts` | Bun/TS |

### Pakai
```
cp .env.example .env            # isi kata sandi/token (openssl rand -hex 24)
scripts/fetch-openbot.sh        # ambil OpenBot pada commit terkunci → vendor/openbot
scripts/dc up -d --build
scripts/seed.sh                 # pasang profil bot ke Hermes
```
Langkah lengkap + cek di home-lab: [`docs/HOMELAB.md`](docs/HOMELAB.md).

### Dry-run (offline, tanpa Docker daemon)
```
scripts/dryrun.sh
```
Apa yang sudah dan belum terbukti: [`docs/VERIFICATION.md`](docs/VERIFICATION.md). Rencana & fase: [`docs/PLAN.md`](docs/PLAN.md).

### Uji Rakazo (opsional)
Lihat `eval/rakazo/` — konfigurasi aman + checklist perbandingan; jalankan `eval/rakazo/run.sh prepare`.

## Sutradara Video Anti-Slop untuk Rakazo

Agent AI untuk [Rakazo](https://github.com/elie222/rakazo) yang membuat dan memeriksa video (Shorts/Reels/TikTok,
explainer, promo, channel faceless) **tanpa AI slop**: bukan hook generik, bukan b-roll yang tidak menjelaskan apa-apa,
bukan angka karangan, bukan potongan seperti metronom, bukan "jangan lupa like, comment, subscribe".

Generasi gambar/video/suara memakai **fal.ai** dengan kunci Anda sendiri, dan hanya setelah Anda menyetujui rencananya.

### Isi

| Folder | Isi |
|---|---|
| [`rakazo-plugin/`](rakazo-plugin/) | Plugin Rakazo: 6 skill, perintah `/video` dan `/cek-slop`, helper `slop-critic`, MCP fal.ai |
| [`bot/`](bot/) | Instruksi bot (tempel ke Rakazo), deskripsi untuk bot lain, routine opsional, listing botdirectory.ai |
| [`toolkit/`](toolkit/) | `slopguard`: CLI pengukur (lint naskah, caption, ledger shot, QA video, contact sheet, klien fal.ai dengan batas anggaran) |
| [`research/`](research/) | [`REPOS.md`](research/REPOS.md): 153 repo GitHub terverifikasi dalam 14 kategori; [`REFERENCES.md`](research/REFERENCES.md): apa yang diambil dari Remotion, video-use, video-shotcraft, stickman-video-director, hallmark, HyperFrames |
| [`scripts/validate_plugin.py`](scripts/validate_plugin.py) | Validasi plugin terhadap aturan pemasangan Rakazo |
| [`simulation/`](simulation/) | Simulasi ujung-ke-ujung: parser plugin asli Rakazo + komputer bot tiruan + fal.ai tiruan; laporan di [`simulation/output/SIMULATION.md`](simulation/output/SIMULATION.md) |
| [`examples/kopi-pahit/`](examples/kopi-pahit/) | Contoh artefak proyek (naskah bersih vs slop, ledger, caption) |

### Pasang di Rakazo (sekitar 5 menit)

1. **Buat bot**: Create (**+**) → **New bot** → nama `Sutradara Anti-Slop`. Disarankan **Computer: Private**
   (file video dan kunci tidak dibagi ke bot lain).
2. **Pasang plugin**: **Integrations** → **+** → **From GitHub** →
   `https://github.com/Jeaniro07/RepOS/tree/main/rakazo-plugin` → **Preview** → **Connect** (server `fal`) dan **Add skills**.
3. **Instruksi**: buka nama bot → **Advanced** → **Instructions**, tempel isi [`bot/INSTRUCTIONS.md`](bot/INSTRUCTIONS.md).
   Isi **How other bots see it** dengan [`bot/DESCRIPTION.md`](bot/DESCRIPTION.md).
4. **Kunci fal.ai** (pilih satu atau keduanya):
   - Di chat bot: "Siapkan toolkit video." Bot menjalankan skill `video-toolkit-setup`, memasang `slopguard` + ffmpeg
     di komputernya, lalu meminta kunci lewat **kartu terlindung** (disimpan terenkripsi sebagai `$FAL_KEY`).
     Jangan pernah menempel kunci di chat.
   - Atau **Integrations** → **Manage MCP servers** → `fal` → **Advanced** → **Access token** → kunci fal.ai →
     **Use in this bot**.
5. **Approvals**: **Settings → Approvals** → **Ask** atau **Auto**. Bot tetap selalu meminta "ya" sebelum belanja
   fal.ai dan tidak pernah mengunggah.

Lalu coba: `/video 45 detik vertikal: kenapa kopi saya pahit padahal bijinya mahal` atau `/cek-slop` dengan
melampirkan naskah atau video.

### Cara kerja bot

```
brief (tanya sekali, maks 5) → 3 alur cerita → SPEC.md (kata sifat → angka, daftar BANNED)
→ naskah bersumber + slopguard lint-script → ledger shot + rencana generasi fal.ai (MINTA PERSETUJUAN)
→ aset → rakit (ffmpeg / HyperFrames / Remotion / Manim) → slopguard qa + contact sheet + slop-critic (maks 3x)
→ REVIEW.md → serahkan MP4 + SRT + kredit + catatan label AI (TIDAK mengunggah)
```

**Floor** (tidak pernah dilanggar): tidak ada fakta karangan; tidak memalsukan orang/kejadian/bukti nyata; tidak ada
materi tanpa lisensi; tidak mengunggah atau belanja fal.ai tanpa "ya"; tidak menyerahkan video yang gagal FLOOR;
tidak mengaku "sudah menonton"; tidak mengubah file sumber Anda.

**Tangga bahan nyata**: footage Anda → capture produk/halaman asli → data asli jadi grafik → motion/diagram dari kode
→ arsip berlisensi terbuka → baru generatif fal.ai. Lebih dari 60% durasi generatif = peringatan slop.

### Apa yang diukur `slopguard`

| Area | Contoh gate |
|---|---|
| Naskah | klaim tanpa `[n]` (FLOOR), hook "Halo guys", "Di era digital ini", "game changer", pancingan like/subscribe, ritme monoton, terlalu panjang untuk durasi |
| Caption | tumpang tindih, melewati akhir video, > 20 karakter/detik, > 42 karakter/baris, tampil < 0.7 s, emoji |
| Ledger | shot tanpa sumber/lisensi (FLOOR), orang nyata sintetis tanpa izin (FLOOR), > 60% generatif, visual diulang |
| Video | aspek salah, tanpa suara, clipping (FLOOR), loudness di luar -14 ± 2 LUFS, jeda mati > 1.5 s, gambar utama beku > 2.5 s, cut metronom, frame pertama hitam |

### Pasang di komputer sendiri (satu perintah)

**Linux / macOS** (memasang git/python/curl yang belum ada lewat package manager, ffmpeg 8.1, perintah `slopguard`, lalu tes otomatis):
```bash
curl -fsSL https://raw.githubusercontent.com/Jeaniro07/RepOS/main/install.sh | bash
```

**Windows 10/11** (PowerShell; memasang Git dan Python lewat winget bila belum ada, ffmpeg 8.1, perintah `slopguard` di PATH, lalu tes):
```powershell
irm https://raw.githubusercontent.com/Jeaniro07/RepOS/main/install.ps1 | iex
```

Kedua installer tidak pernah meminta atau menyimpan API key. Kunci fal.ai diberikan ke bot Rakazo lewat kartu terlindung.

### Batasan yang perlu Anda tahu

- Plugin Rakazo hanya memasang teks; alat ukur dipasang bot di komputernya sendiri dari repo ini (harus publik).
- `slopguard` mengukur; ia tidak menonton atau mendengar. Lolos semua gate bukan jaminan video bagus.
- Endpoint fal.ai sering berganti nama: bot wajib memverifikasi id, schema, dan harga sebelum rencana generasi.
- Kebijakan platform (label AI, konten "inauthentic") berubah; bot diminta membuka halaman kebijakan terbaru.
