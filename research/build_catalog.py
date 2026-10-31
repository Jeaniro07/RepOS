#!/usr/bin/env python3
"""Build research/REPOS.md and research/repos.json from the catalog below.

Every repo listed was checked to exist on 2026-10-31 with `git ls-remote`
(anonymous, public). Re-check any time with:  python3 research/build_catalog.py --verify
Descriptions are in Indonesian; "ambil" = what this project takes from it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))

# (category, [(repo, description, note)])
CATALOG = [
    ("Referensi utama (yang Anda minta)", [
        ("remotion-dev/remotion", "Video sebagai kode React; punya Agent Skills resmi (remotion-create, remotion-markup, captions, voiceover, render).", "Ambil: aturan layout video (ukuran teks minimum, safe area), calculateMetadata untuk durasi dari voiceover. Lisensi khusus: gratis untuk individu/perusahaan kecil, perusahaan besar butuh Company License."),
        ("browser-use/video-use", "Skill Claude Code untuk mengedit footage mentah lewat percakapan: transkrip word-level + timeline_view PNG, EDL, render, self-eval.", "Ambil: 12 hard rules produksi (caption terakhir, fade 30 ms, potong di batas kata, extract per segmen), loop self-eval maks 3, critic sub-agent, project.md sebagai memori. MIT."),
        ("Vincentwei1021/video-shotcraft", "Skill video promo produk sinematik: 124 kartu resep shot, Remotion, beat sync, sound design, frame QA, final review independen.", "Ambil: aturan estetika berbasis kasus (hold 1 s, kecepatan dari akselerasi, slam layar penuh <= 3x), tiga mode (template/otonom/kolaborasi), audit akhir dengan konteks bersih. Apache-2.0."),
        ("Vincentwei1021/video-talkcraft", "Saudara shotcraft untuk video explainer berbasis voiceover: setiap beat gerak dikunci ke suara.", "Lisensi PolyForm Noncommercial: pemakaian komersial toolkit butuh izin penulis."),
        ("kaomei/stickman-video-director", "Skill video stickman: mode Director (storyboard + prompt per klip) dan Autopilot (ilustrasi + micro-animasi + narasi + caption).", "Ambil: gate 'tidak ada gambar utama diam > 2.5 s', ledger per shot (frasa, ide, aksi, bukti), pass khusus 30 detik pertama, larangan mengarang angka/testimoni demi hook. MIT."),
        ("Nutlope/hallmark", "Skill desain anti-'AI-generated look' dengan sloplint, 50 tema, reviewer konteks bersih.", "Ambil: struktur gate Floor / Reflex / Finish, waiver harus tercatat dengan alasan, 'fabricated pass is itself slop', foto berlisensi terbuka dengan kredit. MIT."),
        ("heygen-com/hyperframes", "HTML/CSS/GSAP dirender deterministik jadi MP4; CLI check/snapshot/render; skill untuk agent.", "Ambil: SPEC.md (setiap kata sifat jadi angka), daftar 'BANNED by default', angka komposisi (teks >= 2.6% sisi pendek, 0.5 s + 0.3 s/kata), review P0/P1/P2, warning dead_stretch/first_frame_empty/film_silent. Apache-2.0."),
    ]),
    ("Ekosistem Rakazo", [
        ("elie222/rakazo", "Platform bot AI self-hosted (alternatif Grok Bot): bot persisten, memori, routines, komputer sandbox, approvals, plugin skills + MCP.", "Target platform. Format plugin: plugin.json + skills/*/SKILL.md + commands/ + agents/ + mcp.json."),
        ("elie222/botdirectory.ai", "Direktori prompt bot untuk Grok Bot dan Rakazo.", "Format listing: bots/<slug>.md (lihat bot/botdirectory-listing.md)."),
        ("PramodDutta/botskills", "Setup bot siap tempel untuk Grok Bot dan Rakazo; tiap listing menyatakan satu aksi yang tidak pernah diambil tanpa pemilik.", "Ambil: konvensi 'aksi yang tidak pernah tanpa Anda' (unggah + belanja fal.ai)."),
        ("cogine-ai/CogineBot", "Grok Bot open-source berbasis Rakazo (WIP).", ""),
        ("nicolaeser/RakazoManager", "CLI untuk memasang dan mengoperasikan Rakazo self-hosted dengan Docker Compose.", ""),
        ("luinbytes/rakazo-android", "Klien Android native komunitas untuk Rakazo.", ""),
        ("ComposioHQ/composio", "Katalog integrasi aplikasi yang didukung Rakazo.", "Untuk menghubungkan YouTube/Drive bila diperlukan (unggah tetap butuh persetujuan)."),
    ]),
    ("fal.ai", [
        ("fal-ai/fal", "SDK Python resmi fal (fal_client) dan serverless.", "Sumber endpoint queue/status/upload yang dipakai slopguard/fal.py."),
        ("fal-ai/fal-js", "SDK JavaScript resmi fal.", "Untuk proyek Remotion/HyperFrames berbasis Node."),
        ("fal-ai-community/skills", "Skill agent resmi komunitas fal: model-routing, fal-prompting, cinematography, storytelling, workflow.", "Sumber tabel endpoint di skills/fal-media/references/fal-models.md."),
        ("fal-ai-community/genmedia-cli", "CLI agent-first untuk fal: cari, run, schema, pricing 1200+ endpoint.", "Opsional: verifikasi schema/harga sebelum rencana generasi."),
        ("raveenb/fal-mcp-server", "MCP server pihak ketiga untuk fal (gambar, video, musik, audio).", "Alternatif bila MCP resmi mcp.fal.ai tidak dipakai."),
        ("piebro/fal-ai-mcp-server", "MCP server pihak ketiga untuk fal.ai.", ""),
    ]),
    ("Agent & skill produksi video", [
        ("calesthio/OpenMontage", "Sistem produksi video agentic open-source: banyak pipeline, tools Python, skill pengetahuan produksi.", "Pembanding arsitektur; lisensi AGPL-3.0 (cek sebelum menggabungkan kode)."),
        ("digitalsamba/claude-code-video-toolkit", "Workspace produksi video untuk Claude Code: naskah, voiceover, musik, visual, render.", ""),
        ("wilwaldon/Claude-Code-Video-Toolkit", "Daftar skill, MCP server dan alat video untuk Claude Code (Remotion, Manim, rekaman layar, FFmpeg).", ""),
        ("hassancs91/claude-faceless-shorts-creator", "Pabrik Shorts faceless berbasis Claude Code: jalur TSX (Remotion), generatif (fal, karakter terkunci), kolase.", "Contoh karakter berulang yang konsisten via fal; tetap perlu gate anti-slop."),
        ("JJenglert1/remotion-claude-video", "Starter kit Remotion + Claude Code dengan skill bawaan.", ""),
        ("kajisho5/ffmpeg-skill", "Skill + MCP: agent mengedit footage dengan FFmpeg lokal lalu mengecek hasilnya sendiri; stdlib Python.", "Pendekatan serupa slopguard (lokal, tanpa API)."),
        ("remotion-dev/skills", "Agent Skills resmi Remotion (npx skills add remotion-dev/skills).", ""),
        ("remotion-dev/template-tiktok", "Template Remotion untuk video vertikal dengan caption ala TikTok.", ""),
        ("remotion-dev/github-unwrapped", "Contoh produksi Remotion skala besar (video personal dari data).", "Contoh 'data asli digambar dengan kode'."),
        ("heygen-com/skills", "Skill HeyGen untuk avatar dan video-edit lewat ffmpeg.", "Avatar hanya dengan persetujuan orang yang ditampilkan."),
        ("HKUDS/ViMax", "Kerangka multi-agent (sutradara, penulis, produser, generator) untuk video multi-shot konsisten.", "Ambil: pemisahan peran; tambahkan gate kebenaran yang tidak ada di sana."),
        ("HKUDS/VideoAgent", "Kerangka all-in-one untuk memahami, mengedit, dan membuat video.", ""),
        ("HITsz-TMG/FilmAgent", "Repo kini berisi VideoClaw: karyawan AI pembuat video kreatif (drama pendek, explainer, avatar).", "README berubah dari FilmAgent asli; cek isi sebelum memakai."),
        ("showlab/MovieAgent", "Generasi film otomatis lewat perencanaan multi-agent CoT (kode riset).", ""),
        ("Huanshere/VideoLingo", "Subtitle, terjemahan, dan dubbing tingkat Netflix untuk video.", "Ambil: segmentasi subtitle per makna, panjang baris."),
        ("krillinai/KrillinAI", "Terjemahan dan dubbing video dengan pemrosesan subtitle.", ""),
    ]),
    ("Mesin render, editing & capture", [
        ("FFmpeg/FFmpeg", "Mesin dasar semua render dan pengukuran (ebur128, silencedetect, blackdetect, freezedetect, loudnorm).", "Dipakai langsung oleh slopguard."),
        ("motion-canvas/motion-canvas", "Animasi vektor dengan kode TypeScript untuk explainer.", ""),
        ("redotvideo/revideo", "Fork Motion Canvas untuk render video terprogram via API.", ""),
        ("ManimCommunity/manim", "Animasi matematika/diagram (versi komunitas).", "Untuk diagram dan grafik yang menjelaskan."),
        ("3b1b/manim", "Manim asli 3Blue1Brown.", ""),
        ("mifi/editly", "Editor video deklaratif (JSON) berbasis Node + ffmpeg.", ""),
        ("mifi/lossless-cut", "Pemotong video lossless (GUI) untuk memilih take.", ""),
        ("WyattBlue/auto-editor", "Memotong bagian diam/tidak bergerak otomatis.", "Hati-hati: memotong otomatis bukan berarti memotong pada makna."),
        ("Breakthrough/PySceneDetect", "Deteksi pergantian scene.", "Alternatif deteksi cut yang lebih akurat dari filter scene ffmpeg."),
        ("Zulko/moviepy", "Editing video dengan Python.", ""),
        ("kkroening/ffmpeg-python", "Binding Python untuk merangkai filter ffmpeg.", ""),
        ("PyAV-Org/PyAV", "Binding Pythonic ke library FFmpeg (decode frame per frame).", ""),
        ("abhiTronix/vidgear", "Framework pemrosesan video Python berperforma tinggi.", ""),
        ("OpenCut-app/OpenCut", "Editor video open-source (sedang ditulis ulang dengan Editor API dan MCP untuk agent).", "Calon target 'edit lanjutan oleh manusia'."),
        ("OpenShot/openshot-qt", "Editor video desktop open-source.", ""),
        ("mltframework/shotcut", "Editor video desktop open-source berbasis MLT.", ""),
        ("olive-editor/olive", "Editor video non-linear open-source.", ""),
        ("yt-dlp/yt-dlp", "Pengunduh video; hanya untuk materi yang hak pakainya Anda miliki.", ""),
        ("microsoft/playwright", "Otomasi browser untuk menangkap layar produk asli.", "Rung 2 tangga bahan nyata: capture halaman/produk asli."),
        ("browser-use/browser-use", "Agent yang mengendalikan browser.", ""),
        ("greensock/GSAP", "Library animasi yang dipakai HyperFrames.", ""),
        ("airbnb/lottie-web", "Render animasi Lottie di web.", ""),
        ("vercel/satori", "HTML/JSX ke SVG (kartu teks, thumbnail).", ""),
    ]),
    ("Anti-slop untuk teks & desain", [
        ("blader/humanizer", "Skill yang menghapus pola tulisan AI berdasarkan 'Signs of AI writing' Wikipedia, dengan voice matching.", "Inspirasi kategori lexicon (bukan disalin)."),
        ("hardikpandya/stop-slop", "Skill untuk menghapus 'AI tells' dari prosa: frasa, struktur, ritme.", ""),
        ("chi-feng/humanizer", "Skill portable (MIT) yang mengganti pola tulisan AI dengan pilihan penulis yang cermat.", ""),
        ("jalaalrd/anti-ai-slop-writing", "Skill dengan 50+ kata dan 35+ frasa terlarang dari riset deteksi AI.", ""),
        ("haidrrrry/humanize-ai-writing", "System prompt + skill untuk berbagai chatbot dengan katalog 'tells'.", ""),
        ("sam-paech/antislop-sampler", "Sampler yang mundur dan mengulang saat model menulis frasa terlarang.", "Ide: larangan frasa di level generasi, bukan hanya lint."),
        ("sam-paech/slop-forensics", "Toolkit mengukur kata/n-gram yang terlalu sering muncul di output LLM dan membangun slop list.", "Cara membangun lexicon slop per channel dari data."),
        ("pbakaus/impeccable", "Kosakata desain untuk agent: critique, audit, menangkap AI slop sebelum rilis.", ""),
        ("Leonxlnx/taste-skill", "Skill 'taste' untuk UI agar tidak generik.", ""),
        ("anthropics/skills", "Skill resmi Anthropic (termasuk frontend-design).", ""),
        ("vercel-labs/web-interface-guidelines", "Pedoman antarmuka web dari Vercel.", ""),
        ("emilkowalski/skills", "Skill desain/animasi dari Emil Kowalski.", "Easing dan gerak yang tidak robotik."),
    ]),
    ("Mengukur kualitas video & audio", [
        ("Netflix/vmaf", "Metrik kualitas video perseptual berbasis referensi.", "Untuk membandingkan encode akhir dengan master."),
        ("VQAssessment/DOVER", "Penilai kualitas video tanpa referensi (estetika + teknis), ICCV 2023.", "Kandidat skor kualitas otomatis tambahan."),
        ("VQAssessment/FAST-VQA-and-FasterVQA", "VQA tanpa referensi yang efisien (ECCV 2022).", "Cek lisensi riset sebelum komersial."),
        ("Vchitect/VBench", "Benchmark kualitas model video generatif (16 dimensi).", "Dimensi berguna: konsistensi subjek, flicker, kualitas estetika."),
        ("EvalCrafter/EvalCrafter", "Toolkit evaluasi video AI dengan 17 metrik objektif (CVPR 2024).", ""),
        ("chaofengc/IQA-PyTorch", "Kumpulan metrik kualitas gambar (pyiqa) untuk menyaring frame/gambar generatif.", ""),
        ("slhck/ffmpeg-normalize", "Normalisasi loudness EBU R128 dengan ffmpeg.", "Alternatif loudnorm dua pass."),
        ("csteinmetz1/pyloudnorm", "Pengukuran loudness ITU-R BS.1770 di Python.", ""),
        ("librosa/librosa", "Analisis audio: tempo, beat, onset untuk memotong di ketukan.", ""),
    ]),
    ("Transkrip word-level & caption", [
        ("m-bain/whisperX", "Whisper + forced alignment untuk timestamp per kata dan diarization.", "Alternatif lokal untuk transkrip word-level."),
        ("jianfch/stable-ts", "Timestamp kata Whisper yang distabilkan; ekspor SRT/ASS.", ""),
        ("SYSTRAN/faster-whisper", "Whisper cepat dengan CTranslate2.", ""),
        ("openai/whisper", "Model ASR Whisper asli.", ""),
        ("ggml-org/whisper.cpp", "Whisper di C/C++ untuk CPU.", ""),
        ("linto-ai/whisper-timestamped", "Timestamp dan confidence per kata untuk Whisper.", ""),
        ("nyrahealth/CrisperWhisper", "ASR verbatim dengan timestamp kata akurat (mempertahankan filler).", "Filler yang tidak dinormalisasi = sinyal editing (video-use)."),
        ("pyannote/pyannote-audio", "Diarization pembicara.", ""),
        ("facebookresearch/demucs", "Pemisahan sumber audio (vokal vs musik).", "Membersihkan suara dari musik bawaan footage."),
        ("tkarabela/pysubs2", "Membaca/menulis SRT, ASS, VTT di Python.", ""),
        ("libass/libass", "Renderer subtitle ASS yang dipakai ffmpeg untuk burn-in.", ""),
    ]),
    ("Deteksi konten AI, provenance & watermark", [
        ("contentauth/c2pa-rs", "SDK C2PA (Content Credentials) Rust, termasuk c2patool.", "Untuk menandai asal-usul dan bagian AI di file akhir."),
        ("contentauth/c2pa-python", "Library Python untuk membaca, memvalidasi, dan menandatangani manifest C2PA.", ""),
        ("contentauth/c2patool", "CLI C2PA (repo lama; pengembangan pindah ke c2pa-rs).", ""),
        ("facebookresearch/videoseal", "Watermark tak terlihat untuk gambar dan video.", ""),
        ("facebookresearch/audioseal", "Watermark audio untuk suara sintetis.", ""),
        ("google-deepmind/synthid-text", "Watermark teks SynthID.", ""),
        ("LongMa-2025/AIGVDBench", "Benchmark deteksi video AI: 440K+ video dari 31 model, 33 detektor.", ""),
        ("MusapYildiz/ai_video_detection_benchmark", "AEGIS: detektor video yang sepenuhnya dibuat AI (bukan deepfake wajah).", "Klaim akurasi dari pembuat; verifikasi sendiri."),
        ("dxhou/AI-Generated-Video-Detection", "Kumpulan paper dan benchmark deteksi video AI (survei vision-language).", ""),
        ("ant-research/Awesome-AIGC-Image-Video-Detection", "Daftar kurasi deteksi gambar/video AI.", ""),
        ("lydonator/slopblock", "Ekstensi browser: pelaporan video AI slop di YouTube secara crowdsourced.", "Cara penonton melihat slop: hindari ciri yang mereka laporkan."),
        ("fluryjanis/Content-Chef", "Ekstensi lokal penyaring video AI, clickbait, dan konten berkualitas rendah di YouTube.", ""),
    ]),
    ("Model gambar/video open-source (opsional, lokal)", [
        ("Lightricks/LTX-Video", "Model video DiT cepat.", ""),
        ("Wan-Video/Wan2.2", "Model video Wan 2.2 (teks/gambar ke video).", ""),
        ("Wan-Video/Wan2.1", "Model video Wan 2.1.", ""),
        ("Tencent-Hunyuan/HunyuanVideo", "Model video HunyuanVideo.", ""),
        ("zai-org/CogVideo", "CogVideoX.", ""),
        ("genmoai/mochi", "Model video Mochi.", ""),
        ("Comfy-Org/ComfyUI", "Antarmuka node untuk pipeline difusi lokal.", ""),
        ("kijai/ComfyUI-WanVideoWrapper", "Node ComfyUI untuk model Wan.", ""),
        ("guoyww/AnimateDiff", "Animasi dari model gambar difusi.", ""),
        ("KwaiVGI/LivePortrait", "Animasi potret dari video penggerak.", "Hanya dengan izin orang di potret."),
        ("bytedance/LatentSync", "Lip-sync berbasis difusi laten.", "Hanya dengan izin."),
        ("TMElyralab/MuseTalk", "Lip-sync real-time.", "Hanya dengan izin."),
        ("OpenTalker/SadTalker", "Kepala bicara dari satu gambar + audio.", "Hanya dengan izin."),
        ("fudan-generative-vision/hallo", "Animasi potret didorong audio.", "Hanya dengan izin."),
        ("xinntao/Real-ESRGAN", "Upscale gambar/video.", ""),
        ("hzwer/Practical-RIFE", "Interpolasi frame (RIFE).", "Jangan dipakai untuk menutupi footage yang memang patah-patah."),
        ("k4yt3x/video2x", "Upscale dan interpolasi video.", ""),
        ("danielgatis/rembg", "Hapus latar gambar.", ""),
        ("ZhengPeng7/BiRefNet", "Segmentasi latar presisi tinggi.", ""),
        ("facebookresearch/sam2", "Segment Anything 2 untuk gambar dan video.", "Masking objek nyata untuk overlay."),
    ]),
    ("Suara, musik & efek suara", [
        ("hexgrad/kokoro", "TTS ringan berkualitas tinggi.", ""),
        ("resemble-ai/chatterbox", "TTS open-source dengan kontrol emosi.", "Juga tersedia di fal (chatterbox multilingual)."),
        ("SWivid/F5-TTS", "TTS flow-matching dengan cloning suara.", "Cloning hanya dengan izin pemilik suara."),
        ("coqui-ai/TTS", "Toolkit TTS (XTTS).", ""),
        ("myshell-ai/OpenVoice", "Cloning suara instan.", "Hanya dengan izin."),
        ("OHF-Voice/piper1-gpl", "TTS lokal cepat Piper (penerus rhasspy/piper).", ""),
        ("fishaudio/fish-speech", "TTS multibahasa.", ""),
        ("2noise/ChatTTS", "TTS untuk dialog.", ""),
        ("FunAudioLLM/CosyVoice", "TTS multibahasa.", ""),
        ("nari-labs/dia", "TTS dialog dengan non-verbal.", ""),
        ("index-tts/index-tts", "TTS zero-shot dengan kontrol durasi.", ""),
        ("facebookresearch/audiocraft", "MusicGen/AudioGen.", ""),
        ("hkchengrex/MMAudio", "Audio/efek suara dari video.", "Juga di fal (mmaudio-v2): SFX yang terikat pada gambar."),
        ("ace-step/ACE-Step", "Model generasi musik.", ""),
        ("MTG/freesound-python", "Klien API Freesound untuk efek suara berlisensi CC.", "Catat lisensi CC di ledger."),
    ]),
    ("Pemahaman video (VLM untuk QA tambahan)", [
        ("QwenLM/Qwen3-VL", "Model vision-language yang bisa membaca video.", "Kandidat 'mata' otomatis untuk menjelaskan frame contact sheet."),
        ("DAMO-NLP-SG/VideoLLaMA3", "LLM multimodal untuk pemahaman video.", ""),
        ("OpenGVLab/InternVL", "Model multimodal open-source.", ""),
    ]),
    ("Pabrik video faceless (pelajari, jangan ditiru mentah-mentah)", [
        ("harry0703/MoneyPrinterTurbo", "Satu klik: topik → naskah LLM → stok footage → TTS → subtitle → video.", "Contoh pipeline yang menghasilkan slop bila tanpa brief, sumber, dan QA."),
        ("FujiwaraChoki/MoneyPrinter", "Otomasi YouTube Shorts dari topik.", "Anti-contoh: stok b-roll generik + TTS."),
        ("RayVentura/ShortGPT", "Framework otomasi konten video pendek.", ""),
        ("gyoridavid/short-video-maker", "TTS + caption otomatis + video latar + musik, dengan MCP/REST.", ""),
        ("SamurAIGPT/AI-Youtube-Shorts-Generator", "Memotong video panjang menjadi Shorts dengan AI.", ""),
        ("SamurAIGPT/Text-To-Video-AI", "Teks ke video dengan stok footage.", ""),
        ("elebumm/RedditVideoMakerBot", "Video dari thread Reddit + TTS.", "Contoh klasik konten repetitif yang disasar kebijakan 'inauthentic content'."),
        ("ClipsAI/clipsai", "Mengubah video panjang menjadi klip pendek (transkrip + segmentasi).", "Berguna bila klip dipilih karena maknanya."),
    ]),
    ("Daftar kurasi", [
        ("showlab/Awesome-Video-Diffusion", "Daftar kurasi model difusi video.", ""),
        ("ChenHsing/Awesome-Video-Diffusion-Models", "Survei model difusi video.", ""),
        ("ComposioHQ/awesome-claude-skills", "Daftar kurasi Claude skills.", ""),
        ("travisvn/awesome-claude-skills", "Daftar kurasi Claude skills.", ""),
    ]),
]


def all_repos():
    for cat, items in CATALOG:
        for repo, desc, note in items:
            yield cat, repo, desc, note


def verify(repos):
    def check(r):
        try:
            res = subprocess.run(
                ["git", "ls-remote", "--exit-code", "-q", f"https://github.com/{r}", "HEAD"],
                capture_output=True, timeout=40, env=dict(os.environ, GIT_TERMINAL_PROMPT="0"),
            )
            return r, res.returncode == 0
        except subprocess.TimeoutExpired:
            return r, False
    with ThreadPoolExecutor(max_workers=6) as ex:
        return dict(ex.map(check, repos))


def main():
    rows = list(all_repos())
    if "--verify" in sys.argv:
        status = verify([r for _, r, _, _ in rows])
        bad = [r for r, ok in status.items() if not ok]
        print(f"{len(status) - len(bad)}/{len(status)} reachable")
        for r in bad:
            print("MISSING", r)
        if bad:
            return 1
    md = [
        "# Katalog repo: agen video anti-slop",
        "",
        f"{len(rows)} repo GitHub dalam {len(CATALOG)} kategori, semuanya dicek ada (publik) pada 2026-10-31 dengan `git ls-remote`.",
        "Cek ulang kapan saja: `python3 research/build_catalog.py --verify`. File ini dibuat dari `build_catalog.py`; ubah di sana.",
        "",
        "Kolom *Ambil / catatan* menjelaskan apa yang dipakai proyek ini dari repo tersebut atau peringatan (lisensi, izin, risiko slop).",
        "Jumlah bintang tidak dicantumkan karena tidak bisa diverifikasi dari sesi ini; lihat langsung di GitHub.",
        "",
        "## Daftar isi",
        "",
    ]
    for cat, items in CATALOG:
        anchor = cat.lower().replace(" ", "-")
        for ch in "()&,/'":
            anchor = anchor.replace(ch, "")
        md.append(f"- [{cat}](#{anchor}) ({len(items)})")
    md.append("")
    for cat, items in CATALOG:
        md += [f"## {cat}", "", "| Repo | Apa itu | Ambil / catatan |", "|---|---|---|"]
        for repo, desc, note in items:
            md.append(f"| [{repo}](https://github.com/{repo}) | {desc} | {note} |")
        md.append("")
    with open(os.path.join(HERE, "REPOS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    data = [{"category": c, "repo": r, "url": f"https://github.com/{r}", "description": d, "note": n} for c, r, d, n in rows]
    with open(os.path.join(HERE, "repos.json"), "w", encoding="utf-8") as fh:
        json.dump({"checked": "2026-10-31", "count": len(data), "repos": data}, fh, indent=2, ensure_ascii=False)
    print(f"wrote REPOS.md and repos.json ({len(rows)} repos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
