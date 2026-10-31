# Katalog repo: agen video anti-slop

153 repo GitHub dalam 14 kategori, semuanya dicek ada (publik) pada 2026-10-31 dengan `git ls-remote`.
Cek ulang kapan saja: `python3 research/build_catalog.py --verify`. File ini dibuat dari `build_catalog.py`; ubah di sana.

Kolom *Ambil / catatan* menjelaskan apa yang dipakai proyek ini dari repo tersebut atau peringatan (lisensi, izin, risiko slop).
Jumlah bintang tidak dicantumkan karena tidak bisa diverifikasi dari sesi ini; lihat langsung di GitHub.

## Daftar isi

- [Referensi utama (yang Anda minta)](#referensi-utama-yang-anda-minta) (7)
- [Ekosistem Rakazo](#ekosistem-rakazo) (7)
- [fal.ai](#fal.ai) (6)
- [Agent & skill produksi video](#agent--skill-produksi-video) (16)
- [Mesin render, editing & capture](#mesin-render-editing--capture) (23)
- [Anti-slop untuk teks & desain](#anti-slop-untuk-teks--desain) (12)
- [Mengukur kualitas video & audio](#mengukur-kualitas-video--audio) (9)
- [Transkrip word-level & caption](#transkrip-word-level--caption) (11)
- [Deteksi konten AI, provenance & watermark](#deteksi-konten-ai-provenance--watermark) (12)
- [Model gambar/video open-source (opsional, lokal)](#model-gambarvideo-open-source-opsional-lokal) (20)
- [Suara, musik & efek suara](#suara-musik--efek-suara) (15)
- [Pemahaman video (VLM untuk QA tambahan)](#pemahaman-video-vlm-untuk-qa-tambahan) (3)
- [Pabrik video faceless (pelajari, jangan ditiru mentah-mentah)](#pabrik-video-faceless-pelajari-jangan-ditiru-mentah-mentah) (8)
- [Daftar kurasi](#daftar-kurasi) (4)

## Referensi utama (yang Anda minta)

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | Video sebagai kode React; punya Agent Skills resmi (remotion-create, remotion-markup, captions, voiceover, render). | Ambil: aturan layout video (ukuran teks minimum, safe area), calculateMetadata untuk durasi dari voiceover. Lisensi khusus: gratis untuk individu/perusahaan kecil, perusahaan besar butuh Company License. |
| [browser-use/video-use](https://github.com/browser-use/video-use) | Skill Claude Code untuk mengedit footage mentah lewat percakapan: transkrip word-level + timeline_view PNG, EDL, render, self-eval. | Ambil: 12 hard rules produksi (caption terakhir, fade 30 ms, potong di batas kata, extract per segmen), loop self-eval maks 3, critic sub-agent, project.md sebagai memori. MIT. |
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | Skill video promo produk sinematik: 124 kartu resep shot, Remotion, beat sync, sound design, frame QA, final review independen. | Ambil: aturan estetika berbasis kasus (hold 1 s, kecepatan dari akselerasi, slam layar penuh <= 3x), tiga mode (template/otonom/kolaborasi), audit akhir dengan konteks bersih. Apache-2.0. |
| [Vincentwei1021/video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft) | Saudara shotcraft untuk video explainer berbasis voiceover: setiap beat gerak dikunci ke suara. | Lisensi PolyForm Noncommercial: pemakaian komersial toolkit butuh izin penulis. |
| [kaomei/stickman-video-director](https://github.com/kaomei/stickman-video-director) | Skill video stickman: mode Director (storyboard + prompt per klip) dan Autopilot (ilustrasi + micro-animasi + narasi + caption). | Ambil: gate 'tidak ada gambar utama diam > 2.5 s', ledger per shot (frasa, ide, aksi, bukti), pass khusus 30 detik pertama, larangan mengarang angka/testimoni demi hook. MIT. |
| [Nutlope/hallmark](https://github.com/Nutlope/hallmark) | Skill desain anti-'AI-generated look' dengan sloplint, 50 tema, reviewer konteks bersih. | Ambil: struktur gate Floor / Reflex / Finish, waiver harus tercatat dengan alasan, 'fabricated pass is itself slop', foto berlisensi terbuka dengan kredit. MIT. |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | HTML/CSS/GSAP dirender deterministik jadi MP4; CLI check/snapshot/render; skill untuk agent. | Ambil: SPEC.md (setiap kata sifat jadi angka), daftar 'BANNED by default', angka komposisi (teks >= 2.6% sisi pendek, 0.5 s + 0.3 s/kata), review P0/P1/P2, warning dead_stretch/first_frame_empty/film_silent. Apache-2.0. |

## Ekosistem Rakazo

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [elie222/rakazo](https://github.com/elie222/rakazo) | Platform bot AI self-hosted (alternatif Grok Bot): bot persisten, memori, routines, komputer sandbox, approvals, plugin skills + MCP. | Target platform. Format plugin: plugin.json + skills/*/SKILL.md + commands/ + agents/ + mcp.json. |
| [elie222/botdirectory.ai](https://github.com/elie222/botdirectory.ai) | Direktori prompt bot untuk Grok Bot dan Rakazo. | Format listing: bots/<slug>.md (lihat bot/botdirectory-listing.md). |
| [PramodDutta/botskills](https://github.com/PramodDutta/botskills) | Setup bot siap tempel untuk Grok Bot dan Rakazo; tiap listing menyatakan satu aksi yang tidak pernah diambil tanpa pemilik. | Ambil: konvensi 'aksi yang tidak pernah tanpa Anda' (unggah + belanja fal.ai). |
| [cogine-ai/CogineBot](https://github.com/cogine-ai/CogineBot) | Grok Bot open-source berbasis Rakazo (WIP). |  |
| [nicolaeser/RakazoManager](https://github.com/nicolaeser/RakazoManager) | CLI untuk memasang dan mengoperasikan Rakazo self-hosted dengan Docker Compose. |  |
| [luinbytes/rakazo-android](https://github.com/luinbytes/rakazo-android) | Klien Android native komunitas untuk Rakazo. |  |
| [ComposioHQ/composio](https://github.com/ComposioHQ/composio) | Katalog integrasi aplikasi yang didukung Rakazo. | Untuk menghubungkan YouTube/Drive bila diperlukan (unggah tetap butuh persetujuan). |

## fal.ai

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [fal-ai/fal](https://github.com/fal-ai/fal) | SDK Python resmi fal (fal_client) dan serverless. | Sumber endpoint queue/status/upload yang dipakai slopguard/fal.py. |
| [fal-ai/fal-js](https://github.com/fal-ai/fal-js) | SDK JavaScript resmi fal. | Untuk proyek Remotion/HyperFrames berbasis Node. |
| [fal-ai-community/skills](https://github.com/fal-ai-community/skills) | Skill agent resmi komunitas fal: model-routing, fal-prompting, cinematography, storytelling, workflow. | Sumber tabel endpoint di skills/fal-media/references/fal-models.md. |
| [fal-ai-community/genmedia-cli](https://github.com/fal-ai-community/genmedia-cli) | CLI agent-first untuk fal: cari, run, schema, pricing 1200+ endpoint. | Opsional: verifikasi schema/harga sebelum rencana generasi. |
| [raveenb/fal-mcp-server](https://github.com/raveenb/fal-mcp-server) | MCP server pihak ketiga untuk fal (gambar, video, musik, audio). | Alternatif bila MCP resmi mcp.fal.ai tidak dipakai. |
| [piebro/fal-ai-mcp-server](https://github.com/piebro/fal-ai-mcp-server) | MCP server pihak ketiga untuk fal.ai. |  |

## Agent & skill produksi video

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | Sistem produksi video agentic open-source: banyak pipeline, tools Python, skill pengetahuan produksi. | Pembanding arsitektur; lisensi AGPL-3.0 (cek sebelum menggabungkan kode). |
| [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) | Workspace produksi video untuk Claude Code: naskah, voiceover, musik, visual, render. |  |
| [wilwaldon/Claude-Code-Video-Toolkit](https://github.com/wilwaldon/Claude-Code-Video-Toolkit) | Daftar skill, MCP server dan alat video untuk Claude Code (Remotion, Manim, rekaman layar, FFmpeg). |  |
| [hassancs91/claude-faceless-shorts-creator](https://github.com/hassancs91/claude-faceless-shorts-creator) | Pabrik Shorts faceless berbasis Claude Code: jalur TSX (Remotion), generatif (fal, karakter terkunci), kolase. | Contoh karakter berulang yang konsisten via fal; tetap perlu gate anti-slop. |
| [JJenglert1/remotion-claude-video](https://github.com/JJenglert1/remotion-claude-video) | Starter kit Remotion + Claude Code dengan skill bawaan. |  |
| [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) | Skill + MCP: agent mengedit footage dengan FFmpeg lokal lalu mengecek hasilnya sendiri; stdlib Python. | Pendekatan serupa slopguard (lokal, tanpa API). |
| [remotion-dev/skills](https://github.com/remotion-dev/skills) | Agent Skills resmi Remotion (npx skills add remotion-dev/skills). |  |
| [remotion-dev/template-tiktok](https://github.com/remotion-dev/template-tiktok) | Template Remotion untuk video vertikal dengan caption ala TikTok. |  |
| [remotion-dev/github-unwrapped](https://github.com/remotion-dev/github-unwrapped) | Contoh produksi Remotion skala besar (video personal dari data). | Contoh 'data asli digambar dengan kode'. |
| [heygen-com/skills](https://github.com/heygen-com/skills) | Skill HeyGen untuk avatar dan video-edit lewat ffmpeg. | Avatar hanya dengan persetujuan orang yang ditampilkan. |
| [HKUDS/ViMax](https://github.com/HKUDS/ViMax) | Kerangka multi-agent (sutradara, penulis, produser, generator) untuk video multi-shot konsisten. | Ambil: pemisahan peran; tambahkan gate kebenaran yang tidak ada di sana. |
| [HKUDS/VideoAgent](https://github.com/HKUDS/VideoAgent) | Kerangka all-in-one untuk memahami, mengedit, dan membuat video. |  |
| [HITsz-TMG/FilmAgent](https://github.com/HITsz-TMG/FilmAgent) | Repo kini berisi VideoClaw: karyawan AI pembuat video kreatif (drama pendek, explainer, avatar). | README berubah dari FilmAgent asli; cek isi sebelum memakai. |
| [showlab/MovieAgent](https://github.com/showlab/MovieAgent) | Generasi film otomatis lewat perencanaan multi-agent CoT (kode riset). |  |
| [Huanshere/VideoLingo](https://github.com/Huanshere/VideoLingo) | Subtitle, terjemahan, dan dubbing tingkat Netflix untuk video. | Ambil: segmentasi subtitle per makna, panjang baris. |
| [krillinai/KrillinAI](https://github.com/krillinai/KrillinAI) | Terjemahan dan dubbing video dengan pemrosesan subtitle. |  |

## Mesin render, editing & capture

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | Mesin dasar semua render dan pengukuran (ebur128, silencedetect, blackdetect, freezedetect, loudnorm). | Dipakai langsung oleh slopguard. |
| [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas) | Animasi vektor dengan kode TypeScript untuk explainer. |  |
| [redotvideo/revideo](https://github.com/redotvideo/revideo) | Fork Motion Canvas untuk render video terprogram via API. |  |
| [ManimCommunity/manim](https://github.com/ManimCommunity/manim) | Animasi matematika/diagram (versi komunitas). | Untuk diagram dan grafik yang menjelaskan. |
| [3b1b/manim](https://github.com/3b1b/manim) | Manim asli 3Blue1Brown. |  |
| [mifi/editly](https://github.com/mifi/editly) | Editor video deklaratif (JSON) berbasis Node + ffmpeg. |  |
| [mifi/lossless-cut](https://github.com/mifi/lossless-cut) | Pemotong video lossless (GUI) untuk memilih take. |  |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | Memotong bagian diam/tidak bergerak otomatis. | Hati-hati: memotong otomatis bukan berarti memotong pada makna. |
| [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | Deteksi pergantian scene. | Alternatif deteksi cut yang lebih akurat dari filter scene ffmpeg. |
| [Zulko/moviepy](https://github.com/Zulko/moviepy) | Editing video dengan Python. |  |
| [kkroening/ffmpeg-python](https://github.com/kkroening/ffmpeg-python) | Binding Python untuk merangkai filter ffmpeg. |  |
| [PyAV-Org/PyAV](https://github.com/PyAV-Org/PyAV) | Binding Pythonic ke library FFmpeg (decode frame per frame). |  |
| [abhiTronix/vidgear](https://github.com/abhiTronix/vidgear) | Framework pemrosesan video Python berperforma tinggi. |  |
| [OpenCut-app/OpenCut](https://github.com/OpenCut-app/OpenCut) | Editor video open-source (sedang ditulis ulang dengan Editor API dan MCP untuk agent). | Calon target 'edit lanjutan oleh manusia'. |
| [OpenShot/openshot-qt](https://github.com/OpenShot/openshot-qt) | Editor video desktop open-source. |  |
| [mltframework/shotcut](https://github.com/mltframework/shotcut) | Editor video desktop open-source berbasis MLT. |  |
| [olive-editor/olive](https://github.com/olive-editor/olive) | Editor video non-linear open-source. |  |
| [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) | Pengunduh video; hanya untuk materi yang hak pakainya Anda miliki. |  |
| [microsoft/playwright](https://github.com/microsoft/playwright) | Otomasi browser untuk menangkap layar produk asli. | Rung 2 tangga bahan nyata: capture halaman/produk asli. |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | Agent yang mengendalikan browser. |  |
| [greensock/GSAP](https://github.com/greensock/GSAP) | Library animasi yang dipakai HyperFrames. |  |
| [airbnb/lottie-web](https://github.com/airbnb/lottie-web) | Render animasi Lottie di web. |  |
| [vercel/satori](https://github.com/vercel/satori) | HTML/JSX ke SVG (kartu teks, thumbnail). |  |

## Anti-slop untuk teks & desain

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [blader/humanizer](https://github.com/blader/humanizer) | Skill yang menghapus pola tulisan AI berdasarkan 'Signs of AI writing' Wikipedia, dengan voice matching. | Inspirasi kategori lexicon (bukan disalin). |
| [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) | Skill untuk menghapus 'AI tells' dari prosa: frasa, struktur, ritme. |  |
| [chi-feng/humanizer](https://github.com/chi-feng/humanizer) | Skill portable (MIT) yang mengganti pola tulisan AI dengan pilihan penulis yang cermat. |  |
| [jalaalrd/anti-ai-slop-writing](https://github.com/jalaalrd/anti-ai-slop-writing) | Skill dengan 50+ kata dan 35+ frasa terlarang dari riset deteksi AI. |  |
| [haidrrrry/humanize-ai-writing](https://github.com/haidrrrry/humanize-ai-writing) | System prompt + skill untuk berbagai chatbot dengan katalog 'tells'. |  |
| [sam-paech/antislop-sampler](https://github.com/sam-paech/antislop-sampler) | Sampler yang mundur dan mengulang saat model menulis frasa terlarang. | Ide: larangan frasa di level generasi, bukan hanya lint. |
| [sam-paech/slop-forensics](https://github.com/sam-paech/slop-forensics) | Toolkit mengukur kata/n-gram yang terlalu sering muncul di output LLM dan membangun slop list. | Cara membangun lexicon slop per channel dari data. |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | Kosakata desain untuk agent: critique, audit, menangkap AI slop sebelum rilis. |  |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | Skill 'taste' untuk UI agar tidak generik. |  |
| [anthropics/skills](https://github.com/anthropics/skills) | Skill resmi Anthropic (termasuk frontend-design). |  |
| [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) | Pedoman antarmuka web dari Vercel. |  |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | Skill desain/animasi dari Emil Kowalski. | Easing dan gerak yang tidak robotik. |

## Mengukur kualitas video & audio

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [Netflix/vmaf](https://github.com/Netflix/vmaf) | Metrik kualitas video perseptual berbasis referensi. | Untuk membandingkan encode akhir dengan master. |
| [VQAssessment/DOVER](https://github.com/VQAssessment/DOVER) | Penilai kualitas video tanpa referensi (estetika + teknis), ICCV 2023. | Kandidat skor kualitas otomatis tambahan. |
| [VQAssessment/FAST-VQA-and-FasterVQA](https://github.com/VQAssessment/FAST-VQA-and-FasterVQA) | VQA tanpa referensi yang efisien (ECCV 2022). | Cek lisensi riset sebelum komersial. |
| [Vchitect/VBench](https://github.com/Vchitect/VBench) | Benchmark kualitas model video generatif (16 dimensi). | Dimensi berguna: konsistensi subjek, flicker, kualitas estetika. |
| [EvalCrafter/EvalCrafter](https://github.com/EvalCrafter/EvalCrafter) | Toolkit evaluasi video AI dengan 17 metrik objektif (CVPR 2024). |  |
| [chaofengc/IQA-PyTorch](https://github.com/chaofengc/IQA-PyTorch) | Kumpulan metrik kualitas gambar (pyiqa) untuk menyaring frame/gambar generatif. |  |
| [slhck/ffmpeg-normalize](https://github.com/slhck/ffmpeg-normalize) | Normalisasi loudness EBU R128 dengan ffmpeg. | Alternatif loudnorm dua pass. |
| [csteinmetz1/pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) | Pengukuran loudness ITU-R BS.1770 di Python. |  |
| [librosa/librosa](https://github.com/librosa/librosa) | Analisis audio: tempo, beat, onset untuk memotong di ketukan. |  |

## Transkrip word-level & caption

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [m-bain/whisperX](https://github.com/m-bain/whisperX) | Whisper + forced alignment untuk timestamp per kata dan diarization. | Alternatif lokal untuk transkrip word-level. |
| [jianfch/stable-ts](https://github.com/jianfch/stable-ts) | Timestamp kata Whisper yang distabilkan; ekspor SRT/ASS. |  |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Whisper cepat dengan CTranslate2. |  |
| [openai/whisper](https://github.com/openai/whisper) | Model ASR Whisper asli. |  |
| [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Whisper di C/C++ untuk CPU. |  |
| [linto-ai/whisper-timestamped](https://github.com/linto-ai/whisper-timestamped) | Timestamp dan confidence per kata untuk Whisper. |  |
| [nyrahealth/CrisperWhisper](https://github.com/nyrahealth/CrisperWhisper) | ASR verbatim dengan timestamp kata akurat (mempertahankan filler). | Filler yang tidak dinormalisasi = sinyal editing (video-use). |
| [pyannote/pyannote-audio](https://github.com/pyannote/pyannote-audio) | Diarization pembicara. |  |
| [facebookresearch/demucs](https://github.com/facebookresearch/demucs) | Pemisahan sumber audio (vokal vs musik). | Membersihkan suara dari musik bawaan footage. |
| [tkarabela/pysubs2](https://github.com/tkarabela/pysubs2) | Membaca/menulis SRT, ASS, VTT di Python. |  |
| [libass/libass](https://github.com/libass/libass) | Renderer subtitle ASS yang dipakai ffmpeg untuk burn-in. |  |

## Deteksi konten AI, provenance & watermark

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [contentauth/c2pa-rs](https://github.com/contentauth/c2pa-rs) | SDK C2PA (Content Credentials) Rust, termasuk c2patool. | Untuk menandai asal-usul dan bagian AI di file akhir. |
| [contentauth/c2pa-python](https://github.com/contentauth/c2pa-python) | Library Python untuk membaca, memvalidasi, dan menandatangani manifest C2PA. |  |
| [contentauth/c2patool](https://github.com/contentauth/c2patool) | CLI C2PA (repo lama; pengembangan pindah ke c2pa-rs). |  |
| [facebookresearch/videoseal](https://github.com/facebookresearch/videoseal) | Watermark tak terlihat untuk gambar dan video. |  |
| [facebookresearch/audioseal](https://github.com/facebookresearch/audioseal) | Watermark audio untuk suara sintetis. |  |
| [google-deepmind/synthid-text](https://github.com/google-deepmind/synthid-text) | Watermark teks SynthID. |  |
| [LongMa-2025/AIGVDBench](https://github.com/LongMa-2025/AIGVDBench) | Benchmark deteksi video AI: 440K+ video dari 31 model, 33 detektor. |  |
| [MusapYildiz/ai_video_detection_benchmark](https://github.com/MusapYildiz/ai_video_detection_benchmark) | AEGIS: detektor video yang sepenuhnya dibuat AI (bukan deepfake wajah). | Klaim akurasi dari pembuat; verifikasi sendiri. |
| [dxhou/AI-Generated-Video-Detection](https://github.com/dxhou/AI-Generated-Video-Detection) | Kumpulan paper dan benchmark deteksi video AI (survei vision-language). |  |
| [ant-research/Awesome-AIGC-Image-Video-Detection](https://github.com/ant-research/Awesome-AIGC-Image-Video-Detection) | Daftar kurasi deteksi gambar/video AI. |  |
| [lydonator/slopblock](https://github.com/lydonator/slopblock) | Ekstensi browser: pelaporan video AI slop di YouTube secara crowdsourced. | Cara penonton melihat slop: hindari ciri yang mereka laporkan. |
| [fluryjanis/Content-Chef](https://github.com/fluryjanis/Content-Chef) | Ekstensi lokal penyaring video AI, clickbait, dan konten berkualitas rendah di YouTube. |  |

## Model gambar/video open-source (opsional, lokal)

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) | Model video DiT cepat. |  |
| [Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2) | Model video Wan 2.2 (teks/gambar ke video). |  |
| [Wan-Video/Wan2.1](https://github.com/Wan-Video/Wan2.1) | Model video Wan 2.1. |  |
| [Tencent-Hunyuan/HunyuanVideo](https://github.com/Tencent-Hunyuan/HunyuanVideo) | Model video HunyuanVideo. |  |
| [zai-org/CogVideo](https://github.com/zai-org/CogVideo) | CogVideoX. |  |
| [genmoai/mochi](https://github.com/genmoai/mochi) | Model video Mochi. |  |
| [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | Antarmuka node untuk pipeline difusi lokal. |  |
| [kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper) | Node ComfyUI untuk model Wan. |  |
| [guoyww/AnimateDiff](https://github.com/guoyww/AnimateDiff) | Animasi dari model gambar difusi. |  |
| [KwaiVGI/LivePortrait](https://github.com/KwaiVGI/LivePortrait) | Animasi potret dari video penggerak. | Hanya dengan izin orang di potret. |
| [bytedance/LatentSync](https://github.com/bytedance/LatentSync) | Lip-sync berbasis difusi laten. | Hanya dengan izin. |
| [TMElyralab/MuseTalk](https://github.com/TMElyralab/MuseTalk) | Lip-sync real-time. | Hanya dengan izin. |
| [OpenTalker/SadTalker](https://github.com/OpenTalker/SadTalker) | Kepala bicara dari satu gambar + audio. | Hanya dengan izin. |
| [fudan-generative-vision/hallo](https://github.com/fudan-generative-vision/hallo) | Animasi potret didorong audio. | Hanya dengan izin. |
| [xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) | Upscale gambar/video. |  |
| [hzwer/Practical-RIFE](https://github.com/hzwer/Practical-RIFE) | Interpolasi frame (RIFE). | Jangan dipakai untuk menutupi footage yang memang patah-patah. |
| [k4yt3x/video2x](https://github.com/k4yt3x/video2x) | Upscale dan interpolasi video. |  |
| [danielgatis/rembg](https://github.com/danielgatis/rembg) | Hapus latar gambar. |  |
| [ZhengPeng7/BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | Segmentasi latar presisi tinggi. |  |
| [facebookresearch/sam2](https://github.com/facebookresearch/sam2) | Segment Anything 2 untuk gambar dan video. | Masking objek nyata untuk overlay. |

## Suara, musik & efek suara

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [hexgrad/kokoro](https://github.com/hexgrad/kokoro) | TTS ringan berkualitas tinggi. |  |
| [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) | TTS open-source dengan kontrol emosi. | Juga tersedia di fal (chatterbox multilingual). |
| [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS) | TTS flow-matching dengan cloning suara. | Cloning hanya dengan izin pemilik suara. |
| [coqui-ai/TTS](https://github.com/coqui-ai/TTS) | Toolkit TTS (XTTS). |  |
| [myshell-ai/OpenVoice](https://github.com/myshell-ai/OpenVoice) | Cloning suara instan. | Hanya dengan izin. |
| [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) | TTS lokal cepat Piper (penerus rhasspy/piper). |  |
| [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) | TTS multibahasa. |  |
| [2noise/ChatTTS](https://github.com/2noise/ChatTTS) | TTS untuk dialog. |  |
| [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice) | TTS multibahasa. |  |
| [nari-labs/dia](https://github.com/nari-labs/dia) | TTS dialog dengan non-verbal. |  |
| [index-tts/index-tts](https://github.com/index-tts/index-tts) | TTS zero-shot dengan kontrol durasi. |  |
| [facebookresearch/audiocraft](https://github.com/facebookresearch/audiocraft) | MusicGen/AudioGen. |  |
| [hkchengrex/MMAudio](https://github.com/hkchengrex/MMAudio) | Audio/efek suara dari video. | Juga di fal (mmaudio-v2): SFX yang terikat pada gambar. |
| [ace-step/ACE-Step](https://github.com/ace-step/ACE-Step) | Model generasi musik. |  |
| [MTG/freesound-python](https://github.com/MTG/freesound-python) | Klien API Freesound untuk efek suara berlisensi CC. | Catat lisensi CC di ledger. |

## Pemahaman video (VLM untuk QA tambahan)

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [QwenLM/Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) | Model vision-language yang bisa membaca video. | Kandidat 'mata' otomatis untuk menjelaskan frame contact sheet. |
| [DAMO-NLP-SG/VideoLLaMA3](https://github.com/DAMO-NLP-SG/VideoLLaMA3) | LLM multimodal untuk pemahaman video. |  |
| [OpenGVLab/InternVL](https://github.com/OpenGVLab/InternVL) | Model multimodal open-source. |  |

## Pabrik video faceless (pelajari, jangan ditiru mentah-mentah)

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | Satu klik: topik → naskah LLM → stok footage → TTS → subtitle → video. | Contoh pipeline yang menghasilkan slop bila tanpa brief, sumber, dan QA. |
| [FujiwaraChoki/MoneyPrinter](https://github.com/FujiwaraChoki/MoneyPrinter) | Otomasi YouTube Shorts dari topik. | Anti-contoh: stok b-roll generik + TTS. |
| [RayVentura/ShortGPT](https://github.com/RayVentura/ShortGPT) | Framework otomasi konten video pendek. |  |
| [gyoridavid/short-video-maker](https://github.com/gyoridavid/short-video-maker) | TTS + caption otomatis + video latar + musik, dengan MCP/REST. |  |
| [SamurAIGPT/AI-Youtube-Shorts-Generator](https://github.com/SamurAIGPT/AI-Youtube-Shorts-Generator) | Memotong video panjang menjadi Shorts dengan AI. |  |
| [SamurAIGPT/Text-To-Video-AI](https://github.com/SamurAIGPT/Text-To-Video-AI) | Teks ke video dengan stok footage. |  |
| [elebumm/RedditVideoMakerBot](https://github.com/elebumm/RedditVideoMakerBot) | Video dari thread Reddit + TTS. | Contoh klasik konten repetitif yang disasar kebijakan 'inauthentic content'. |
| [ClipsAI/clipsai](https://github.com/ClipsAI/clipsai) | Mengubah video panjang menjadi klip pendek (transkrip + segmentasi). | Berguna bila klip dipilih karena maknanya. |

## Daftar kurasi

| Repo | Apa itu | Ambil / catatan |
|---|---|---|
| [showlab/Awesome-Video-Diffusion](https://github.com/showlab/Awesome-Video-Diffusion) | Daftar kurasi model difusi video. |  |
| [ChenHsing/Awesome-Video-Diffusion-Models](https://github.com/ChenHsing/Awesome-Video-Diffusion-Models) | Survei model difusi video. |  |
| [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | Daftar kurasi Claude skills. |  |
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | Daftar kurasi Claude skills. |  |
