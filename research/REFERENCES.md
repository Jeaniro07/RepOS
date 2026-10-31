# Catatan referensi: apa yang diambil dari setiap repo

Dibaca langsung dari kode/README masing-masing repo pada 2026-10-31 (clone dangkal). Tidak ada teks yang
disalin mentah; aturan dirumuskan ulang dan dikaitkan ke tempat ia dipakai di proyek ini.

## remotion-dev/remotion

**Apa:** video sebagai komponen React; dirender frame demi frame. Paket `packages/skills` berisi Agent Skills
resmi: `remotion-create`, `remotion-markup` (audio, captions, voiceover dengan ElevenLabs + `calculateMetadata`,
transitions, fonts, silence-detection, sfx), `remotion-render`, `remotion-best-practices`, dll.

**Diambil:**
- Aturan layout video: "desain video, bukan halaman web"; satu hal yang dilihat pertama per scene; safe area
  (>= 80 px samping, 100 px atas/bawah pada lebar 1080); ukuran minimum judul/teks penting → `SPEC.md` (TYPE) dan
  `video-assembly`.
- Durasi komposisi mengikuti voiceover, bukan sebaliknya → aturan "jangan mempercepat narasi" di `video-assembly`.

**Tidak diambil / peringatan:** lisensi Remotion dua tingkat (gratis untuk individu & perusahaan kecil, Company
License untuk perusahaan lebih besar) → disebut di `video-assembly` dan `REPOS.md`.

## browser-use/video-use

**Apa:** skill Claude Code untuk mengedit footage mentah lewat chat. LLM tidak menonton video; ia membaca transkrip
word-level yang dipadatkan (`takes_packed.md`) dan meminta `timeline_view` PNG hanya di titik keputusan.
Alur: Transcribe → Pack → LLM → EDL → Render → Self-eval (maks 3).

**Diambil:**
- 12 hard rules produksi (caption paling akhir, extract per segmen lalu concat lossless, fade 30 ms di setiap
  batas, overlay digeser `setpts`, SRT di timeline output, tidak memotong di dalam kata, padding 30-200 ms,
  transkrip word-level verbatim, cache transkrip) → `skills/video-assembly`.
- "Teks + visual sesuai permintaan, bukan dump frame" → contact sheet `overview.jpg` + `cuts.jpg` di `slopguard qa`.
- Self-eval di setiap batas potongan, ukur loudness (`ebur128`), dan "kamu tidak bisa mendengar: katakan" →
  `videoqa.py`, Floor #6.
- Critic sub-agent yang diminta "roast, not praise" → `agents/slop-critic.md`.
- `project.md` sebagai memori sesi → `slopguard init`.
- Konfirmasi strategi sebelum memotong → mode Bareng.

## Vincentwei1021/video-shotcraft (yang Anda sebut "video-shortcraft")

**Apa:** skill promo produk sinematik. 124 kartu resep shot dengan demo Remotion, template Ink Press, beat sync
(librosa), sound design dari Freesound, QA per frame, final review oleh subagent konteks bersih, ekspor JianYing.

**Diambil:**
- Aturan estetika berbasis kasus nyata: informasi kunci harus "bernapas" (hold >= 1 s untuk wordmark), kecepatan
  dari akselerasi bukan gerak linear, satu teknik animasi hanya sekali jadi bintang, kejutan layar penuh di ketukan
  maksimal 3 kali per film, SFX hanya pada aksi yang terlihat, dua versi (dengan/tanpa BGM) → `banned-defaults.md`,
  `video-assembly`.
- Tampilkan produk nyata dengan screenshot asli, bukan UI tiruan → tangga bahan nyata (rung 2).
- Tiga mode (template / otonom / kolaborasi) → mode Bareng vs Autopilot.
- Data sensitif di layar harus dipalsukan/disamarkan sebelum capture → Floor (tidak memalsukan bukti) + review.

**Saudaranya:** `video-talkcraft` untuk explainer berbasis narasi, lisensi PolyForm Noncommercial (komersial butuh izin).

## kaomei/stickman-video-director

**Apa:** skill video stickman. Mode A (Director): proposal sutradara + prompt per klip 10 detik dengan alur 5 tahap.
Mode B (Autopilot): ilustrasi + micro-animasi + narasi + caption + SFX dirender lokal.

**Diambil (dari `autopilot-production-qa.md`):**
- Tidak ada inaktivitas gambar utama > 2.5 s; pergantian subtitle, zoom/pan seluruh frame, noise dekoratif tidak
  dihitung sebagai gerak; detektor freeze hanya alat bantu → gate `picture.frozen` (mengecualikan pita caption dan
  UI platform) + teks fix-nya.
- Ledger per shot (frasa, ide, subjek/aksi, bukti/sumber, caption, SFX) → `ledger.csv` + `slopguard check-ledger`.
- Pass khusus untuk 30 detik pertama; jangan mengarang angka, popularitas, testimoni, atau kemampuan produk untuk
  menguatkan hook → Floor #1, `antislop-script`.
- Screenshot harus asli dan terbaca di frame akhir; diagram tidak boleh menyamar sebagai rekaman layar → tangga bahan nyata.
- Caption dikelompokkan per makna; grouping otomatis hanya draf → `video-assembly` (Captions).

## Nutlope/hallmark

**Apa:** skill desain yang "menolak terlihat dibuat AI". Floor yang tidak bisa ditawar, gate Reflex yang boleh
di-waive dengan alasan tercatat, Finish yang tidak memblokir; `sloplint` di browser nyata; reviewer konteks bersih.

**Diambil:**
- Struktur tiga tingkat FLOOR / REFLEX / FINISH → `slopguard/report.py`, `references/floor.md`.
- Waiver harus punya alasan nyata dan tercatat; FLOOR tidak bisa di-waive → `load_waivers` (alasan < 8 karakter
  ditolak) dan `apply_waivers` (FLOOR diabaikan).
- "A fabricated pass is itself slop" → Floor #6.
- Tidak pernah ada metrik, testimoni, atau logo wall karangan → Floor #1.
- Foto berlisensi terbuka dengan kredit, bukan situs stok yang melarang alat AI → rung 5 + lisensi di ledger.

## heygen-com/hyperframes

**Apa:** framework HTML/CSS/GSAP yang dirender deterministik menjadi MP4, dengan CLI (`check`, `snapshot --review`,
`render`, `audio`) dan skill agent (`hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `media-use`).

**Diambil:**
- `SPEC.md`: setiap kata sifat jadi angka (premium, modern, clean, dynamic, cinematic → nilai konkret) → template
  `SPEC.md` di `slopguard init`.
- Daftar "BANNED by default" (void gelap, glow/partikel, gradien ungu-biru, semua fade+slide up, tiga kartu sejajar,
  logo di pojok) yang terus bertambah setelah render pertama → `banned-defaults.md`.
- Angka komposisi: hero >= 40% frame, satu gerakan utama per shot, sesuatu yang baru setiap 2-4 s, teks >= 2.6% sisi
  pendek, tahan 0.5 s + 0.3 s per kata → `SPEC.md`, `antislop-video-director`.
- Warning terukur `dead_stretch`, `first_frame_empty`, `film_silent`, `line_unread` → gate `picture.frozen`,
  `picture.first-frame`, `audio.missing`, `captions.reading-speed`.
- Review sebagai sutradara keras: deskripsikan setiap frame seperti orang asing, catatan P0/P1/P2 berformat
  `t=... · where · problem → change · what stays`, jangan memberi skor → `references/review.md`, `slop-critic`.

## fal.ai (diminta: gunakan API key fal.ai)

- Protokol dari kode `fal-ai/fal` (`fal_client/client.py`): submit ke `https://queue.fal.run/<endpoint>`, header
  `Authorization: Key <FAL_KEY>`, polling `status_url`, ambil `response_url`; upload via
  `https://rest.fal.ai/storage/upload/initiate?storage_type=gcs` lalu PUT → `toolkit/slopguard/fal.py`
  (diuji dengan server tiruan, karena fal.ai tidak bisa diakses dari sesi pembuatan ini).
- MCP resmi `https://mcp.fal.ai/mcp` (streamable HTTP, bearer key) → `rakazo-plugin/mcp.json`.
- Routing endpoint dari `fal-ai-community/skills` (`model-routing`) → `skills/fal-media/references/fal-models.md`,
  dengan kewajiban verifikasi id + schema + harga sebelum dipakai.
- Kunci di Rakazo: command variable `fal-key` → `$FAL_KEY` (dokumentasi Rakazo `bot-secrets.md`), tidak pernah di chat.

## elie222/rakazo (platform target)

- Plugin dari GitHub: `plugin.json` (schema agent-plugins 1.1.0) + `skills/<name>/SKILL.md` + `commands/` (jadi
  `/nama`) + `agents/` (jadi skill yang memanggil `run_subagent`) + `mcp.json`. Skrip di plugin tidak dijalankan,
  hanya teks (maks 40 file referensi / 400 KB per skill) → toolkit dipasang terpisah di komputer bot.
- Komputer bot: Debian, uid 1000, tanpa apt; ada python3, git, curl, uv, imagemagick; tanpa ffmpeg/Node →
  `toolkit/setup.sh` mengunduh ffmpeg statis ke home.
- Approvals (Ask/Auto/Never ask) + konvensi botskills "satu aksi yang tidak pernah tanpa Anda" → unggah dan belanja fal.ai.

## Riset ronde 2 (2026-10-31): standar, studi, dan video YouTube

Dipakai untuk penyempurnaan `slopguard` dan skill. Sebagian besar sumber kebijakan adalah liputan pers;
skill menyuruh bot memeriksa halaman resmi sebelum mengutipnya ke pengguna.

| Sumber | Apa isinya | Dipakai di |
|---|---|---|
| [Netflix Timed Text Style Guide: General Requirements](https://backlothelp.netflix.com/hc/en-us/articles/215758617), [Subtitle Timing Guidelines](https://backlothelp.netflix.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines), [Indonesian guide](https://backlothelp.netflix.com/hc/en-us/articles/216009727) | Durasi 5/6 s – 7 s, jeda minimal 2 frame, out-time 2 frame sebelum shot change atau 12+ frame darinya; Indonesia 42 karakter/baris, 17 karakter/detik (dewasa) | `build.captions_from_words`, `captions.check_captions` (kecepatan per bahasa, `captions.gap`, `captions.short`), `captions.near_cut_findings` |
| [W3C CSS thread oleh Nigel Megitt](https://lists.w3.org/Archives/Public/public-css-archive/2023Oct/0016.html), crate [subtitler](https://docs.rs/crate/subtitler/1.2.0/source/src/normalize.rs) | Menyeimbangkan baris subtitle tidak cukup dengan panjang saja; struktur kalimat harus ikut | Pemisahan kalimat seimbang (DP) + kata yang harus menempel ke kata berikutnya (preposisi, bilangan) |
| [VBench (arXiv 2311.17982)](https://arxiv.org/pdf/2311.17982) | Dimensi "temporal flickering" untuk video generatif | Gate `picture.flicker` (osilasi luma per frame) |
| [Shaib et al., Measuring AI "Slop" in Text (arXiv 2509.19163)](https://arxiv.org/abs/2509.19163v1) | 7 dimensi slop; relevansi, kepadatan informasi, nada = prediktor terkuat; teks manusia pun bisa slop | Gate `script.generic` (spesifik per 100 kata), peta gate ↔ dimensi di `floor.md` |
| Panduan safe zone: [Remotion social safe zones](https://www.remotion.dev/elements/overlays/social-safe-zones/), [reap.video](https://reap.video/blog/short-form-video-safe-zones), [adaptlypost](https://adaptlypost.com/blog/social-media-safe-zones-2026-complete-guide) | UI menutupi sekitar atas 120-200, bawah 250-370, kanan 120-164, kiri 50-60 px; kotak aman bersama ~900x1400 | `sheet.safe_zone_sheet` → `safezones.jpg` (perkiraan, bukan spesifikasi resmi) |
| Kebijakan YouTube: [inauthentic content, Juli 2025](https://www.plagiarismtoday.com/2025/07/08/youtube-targets-inauthentic-content/), [label altered/synthetic, Maret 2024](https://9to5google.com/2024/03/18/youtube-altered-content-disclosure/), [label AI otomatis + C2PA, Mei 2026](https://c2paviewer.com/articles/youtube-ai-labels-c2pa), ["Captured with a camera"](https://www.techloy.com/youtube-introduces-new-label-to-verify-authentic-video-content/) | Monetisasi konten massal/repetitif dihentikan; label AI otomatis; label kamera berbasis C2PA 2.1 | `references/platform.md`, catatan pengungkapan AI di REVIEW |
| [Kotaku: YouTube salah menandai Kurzgesagt sebagai AI slop](https://kotaku.com/youtube-mistakenly-penalizes-popular-science-channel-kurzgesagt-for-ai-generated-slop-2000722702), [Dexerto](https://www.dexerto.com/youtube/youtubes-ai-slop-detector-incorrectly-targets-kurzgesagt-as-other-creators-fear-same-fate-3395930/) | Detektor slop platform juga salah menandai video buatan manusia | "Provenance pack" di langkah Deliver (ledger, sumber, daftar file mentah, QA) untuk banding |
| [Kapwing AI Slop Report](https://www.kapwing.com/blog/ai-slop-report-the-global-rise-of-low-quality-ai-videos/) | 21-33% feed YouTube akun baru berisi AI slop/brainrot (Desember 2025) | Konteks README |
| YouTube: [Last Week Tonight, "AI Slop" (HBO)](https://www.youtube.com/watch?v=TWpg1RmzAbc); Kurzgesagt, "AI Slop Is Killing Our Channel" (2025, [TheTVDB](https://thetvdb.com/series/kurzgesagt-in-a-nutshell/episodes/11383775)) | Cara penonton dan kreator melihat slop: spam yang meniru konten, informasi tanpa sumber | Penekanan pada sumber, ide per shot, dan larangan konten massal |
| Halaman model fal: [Seedance 2.0 i2v](https://fal.ai/models/bytedance/seedance-2.0/image-to-video/api), [Nano Banana Pro](https://fal.ai/learn/tools/how-to-use-nano-banana-pro), [ElevenLabs di fal](https://fal.ai/elevenlabs) | ID endpoint dan harga indikatif | `fal-models.md`, `slopguard fal plan` |
| Artikel Indonesia tentang ciri tulisan AI: [detik](https://www.detik.com/bali/berita/d-7905724/6-cara-mendeteksi-tulisan-buatan-ai), [eraspace](https://eraspace.com/artikel/post/ciri-ciri-tulisan-ai-yang-mudah-dikenali-tanpa-perlu-tools) | Frasa pembuka klise ("patut dicatat", "sebagaimana diketahui"), nada kaku, pengulangan | Lexicon Indonesia tambahan (frasa ini wajar dipakai manusia; yang dihitung adalah kepadatannya) |
