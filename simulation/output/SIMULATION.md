# Simulasi: bot Rakazo memakai plugin antislop-video

- Tanggal: 2026-10-31 14:18 UTC
- Repo yang di-clone bot: `https://github.com/Jeaniro07/RepOS` ref `claude/keen-einstein-1e7dc9`
- Hasil: **39/39 langkah sesuai harapan**
- Skill terpasang menurut parser Rakazo: antislop-script, antislop-video-director, cek-slop, fal-media, slop-critic, video, video-assembly, video-qa, video-toolkit-setup

Nyata: parser plugin Rakazo, clone dari GitHub, setup.sh + ffmpeg statis, semua perintah slopguard, semua render ffmpeg.
Simulasi: komputer bot (user non-root, Python 3.11, tanpa ffmpeg/node/apt/pip/uv), server fal.ai tiruan (protokol sama, media dibuat lokal),
footage pengguna (klip placeholder berlabel), dan tulisan agent (brief/naskah dari `simulation/scenario/`). LLM dan run slop-critic tidak dijalankan.

## Langkah

| # | Pelaku | Skill | Langkah | Exit (harapan) | Hasil |
|---|---|---|---|---|---|
| 1 | rakazo | Integrations → From GitHub | Rakazo Preview: parsePluginDirectory (elie222/rakazo@4607914) | 0 (0) | ✅ |
| 2 | rakazo | - | validate_plugin.py (batas ukuran & format) | 0 (0) | ✅ |
| 3 | sim | - | Komputer bot siap: user non-root, Python 3.11, tanpa ffmpeg/node/apt/pip/uv di PATH | - | ✅ |
| 4 | bot | - | Cek awal: ffmpeg memang tidak ada | 0 (0) | ✅ |
| 5 | bot | video-toolkit-setup | video-toolkit-setup: clone repo dari GitHub + setup.sh + doctor | 0 (0) | ✅ |
| 6 | bot | video-toolkit-setup | ffmpeg kini bisa dipanggil langsung (untuk video-assembly) | 0 (0) | ✅ |
| 7 | bot | video-toolkit-setup | Tes toolkit di komputer bot | 0 (0) | ✅ |
| 8 | user | fal-media | request_secret {name: fal-key, auth: command} → pengguna menyimpan kunci di kartu terlindung | - | ✅ |
| 9 | bot | video-toolkit-setup | doctor melihat $FAL_KEY tanpa menampilkannya | 0 (0) | ✅ |
| 10 | user | video (command) | /video 20 detik vertikal: kenapa kopi saya pahit padahal bijinya mahal | - | ✅ |
| 11 | bot | antislop-video-director | slopguard init proyek | 0 (0) | ✅ |
| 12 | bot | antislop-video-director | Brief diisi, 3 alur cerita diusulkan, pengguna memilih alur 1; SPEC.md ditulis | - | ✅ |
| 13 | bot | antislop-script | Naskah draf 1 → lint (harus DIBLOKIR) | 1 (1) | ✅ |
| 14 | bot | cek-slop (command) | /cek-slop pada draf 1 (ringkas) | 1 (1) | ✅ |
| 15 | bot | antislop-script | Naskah draf 2 → lint (harus CLEAR) | 0 (0) | ✅ |
| 16 | bot | fal-media | fal plan dengan harga TTS kosong (harus menolak terlihat lengkap) | 2 (2) | ✅ |
| 17 | bot | fal-media | fal plan lengkap → GENERATION_PLAN.md untuk persetujuan | 0 (0) | ✅ |
| 18 | bot | antislop-video-director | Ledger rencana → check-ledger | 0 (0) | ✅ |
| 19 | bot | fal-media | fal run TANPA --confirm (harus ditolak, tanpa panggilan jaringan) | 3 (3) | ✅ |
| 20 | user | fal-media | Pengguna: “Ya, setuju rencana 4 panggilan.” | - | ✅ |
| 21 | bot | fal-media | fal 1/4: TTS narasi | 0 (0) | ✅ |
| 22 | bot | fal-media | fal 2/4: transkrip per kata (file lokal di-upload otomatis) | 0 (0) | ✅ |
| 23 | bot | fal-media | fal 3/4: still shot 4 | 0 (0) | ✅ |
| 24 | bot | fal-media | fal 4/4: gerak dari still | 0 (0) | ✅ |
| 25 | bot | fal-media | Panggilan ke-5 di luar rencana (harus ditolak oleh batas anggaran) | 3 (3) | ✅ |
| 26 | bot | fal-media | Lihat hasil generatif di contact sheet sebelum dipakai | 0 (0) | ✅ |
| 27 | sim | - | (simulasi) footage pengguna: assets/pour.mp4 | 0 (0) | ✅ |
| 28 | sim | - | (simulasi) footage pengguna: assets/kettle.mp4 | 0 (0) | ✅ |
| 29 | sim | - | (simulasi) footage pengguna: assets/taste.mp4 | 0 (0) | ✅ |
| 30 | bot | video-assembly | Potongan diambil dari jeda antar-kalimat di transkrip: [0.0, 4.708, 7.18, 12.32, 16.979, 19.752] | - | ✅ |
| 31 | bot | video-assembly | Caption dari timestamp kata, ditempel ke titik potong (slopguard captions --cuts) | 0 (0) | ✅ |
| 32 | bot | video-assembly | Render v1: shot per segmen → concat -c copy → caption TERAKHIR (pass sendiri) → mux audio → master -14 LUFS | 0 (0) | ✅ |
| 33 | bot | video-qa | QA pass 1 (harus menemukan kartu judul diam di shot 3) | 2 (2) | ✅ |
| 34 | bot | video-qa | Perbaikan: shot 3 diubah dari kartu diam menjadi diagram yang bergerak sesuai narasi (batang 'senyawa pahit' terisi) | - | ✅ |
| 35 | bot | video-assembly | Render v2: shot per segmen → concat -c copy → caption TERAKHIR (pass sendiri) → mux audio → master -14 LUFS | 0 (0) | ✅ |
| 36 | bot | video-qa | QA pass 2 | 0 (0) | ✅ |
| 37 | bot | video-qa | Bahan untuk helper slop-critic tersedia (run_subagent dijalankan oleh Rakazo) | 0 (0) | ✅ |
| 38 | bot | antislop-video-director | Serahkan: final.mp4 + SRT + REVIEW + ledger (tanpa mengunggah) | 0 (0) | ✅ |
| 39 | sim | Floor #4 | Audit keamanan: anggaran, kunci, publikasi | 0 (0) | ✅ |

## Audit

```json
{
  "fal_submits_total": 4,
  "fal_submits_before_approval": 0,
  "fal_endpoints": [
    "fal-ai/elevenlabs/tts/eleven-v3",
    "fal-ai/elevenlabs/speech-to-text/scribe-v2",
    "fal-ai/nano-banana-pro",
    "bytedance/seedance-2.0/image-to-video"
  ],
  "requests_without_key": 0,
  "files_or_outputs_containing_key": [],
  "upload_or_publish_commands": "none (no YouTube/TikTok/IG tools exist or were called)"
}
```

## QA akhir

Verdict: **CLEAR: no open FLOOR or REFLEX findings. Still review it with fresh eyes.**

- size: 1080x1920
- duration (s): 19.8
- fps: 30.0
- video codec: h264
- audio: aac 48000 Hz
- target duration (s): 20
- bits per pixel: 0.029
- integrated loudness (LUFS): -14.0
- true peak (dBTP): -1.5
- loudness range (LU): 1.7
- dead-air gaps: 0
- frozen share of runtime: 0%
- flicker stretches: 0
- first frame luma / range: 133 / 56
- cuts detected: 3
- mean shot length (s): 4.95
- captions: reading-speed limit (chars/s): 17.0
- captions: cues: 6
- captions: mean reading speed (chars/s): 10.4
- ledger: shots: 5
- ledger: runtime in ledger (s): 19.75
- ledger: runtime by source: footage 50%, code 26%, generated 24%

Contact sheet: [overview.jpg](overview.jpg) · [cuts.jpg](cuts.jpg) · [safezones.jpg](safezones.jpg) · rencana biaya: [GENERATION_PLAN.md](GENERATION_PLAN.md) · video hasil (diperkecil): [final-360p.mp4](final-360p.mp4)

## Log per langkah

### 1. Rakazo Preview: parsePluginDirectory (elie222/rakazo@4607914)

```bash
node … preview.mjs rakazo-plugin
```
```text
{
  "name": "antislop-video",
  "version": "0.1.0",
  "format": "agent-plugins",
  "skills": [
    {
      "name": "antislop-script",
      "files": 0
    },
    {
      "name": "antislop-video-director",
      "files": 4
    },
    {
      "name": "cek-slop",
      "files": 0
    },
    {
      "name": "fal-media",
      "files": 1
    },
    {
      "name": "slop-critic",
      "files": 0
    },
    {
      "name": "video",
      "files": 0
    },
    {
      "name": "video-assembly",
      "files": 0
    },
    {
      "name": "video-qa",
      "files": 0
    },
    {
      "name": "video-toolkit-setup",
      "files": 0
    }
  ],
  "mcpServers": [
    {
      "name": "fal",
      "transport": "streamable_http",
      "endpoint": "https://mcp.fal.ai/mcp",
      "headers": {}
    }
  ],
  "skipped": [],
  "builtinNames": []
}
```

### 2. validate_plugin.py (batas ukuran & format)

```bash
python3 scripts/validate_plugin.py rakazo-plugin
```
```text
/home/user/RepOS/rakazo-plugin: 17 files, 52550 bytes, 7 skills/agents
OK
```

### 3. Komputer bot siap: user non-root, Python 3.11, tanpa ffmpeg/node/apt/pip/uv di PATH


### 4. Cek awal: ffmpeg memang tidak ada

```bash
command -v ffmpeg || echo 'ffmpeg: tidak ada'; python3 --version; id -u
```
```text
ffmpeg: tidak ada
Python 3.11.18
1500
```

### 5. video-toolkit-setup: clone repo dari GitHub + setup.sh + doctor

```bash
REF="${ANTISLOP_REF:-main}"
if [ -d ~/antislop/RepOS/.git ]; then git -C ~/antislop/RepOS pull --ff-only; \
else mkdir -p ~/antislop && git clone --depth 1 --branch "$REF" https://github.com/Jeaniro07/RepOS ~/antislop/RepOS; fi
bash ~/antislop/RepOS/toolkit/setup.sh
slopguard doctor
```
```text
downloading https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n8.1-latest-linux64-gpl-8.1.tar.xz (about 150 MB)...
installed /tmp/antislop-sim-dbnhxoiu/home/.local/share/slopguard/bin/ffmpeg
installed /tmp/antislop-sim-dbnhxoiu/home/.local/share/slopguard/bin/ffprobe
slopguard 0.1.0  python 3.11.18
ffmpeg : /tmp/antislop-sim-dbnhxoiu/home/.local/bin/ffmpeg  (version n8.1.3-27-g8dca1586f4-20261031)
ffprobe: /tmp/antislop-sim-dbnhxoiu/home/.local/bin/ffprobe
FAL_KEY: not set (needed only for fal generation)
filters: all present
slopguard 0.1.0  python 3.11.18
ffmpeg : /tmp/antislop-sim-dbnhxoiu/home/.local/bin/ffmpeg  (version n8.1.3-27-g8dca1586f4-20261031)
ffprobe: /tmp/antislop-sim-dbnhxoiu/home/.local/bin/ffprobe
FAL_KEY: not set (needed only for fal generation)
filters: all present

Cloning into '/tmp/antislop-sim-dbnhxoiu/home/antislop/RepOS'...
```

### 6. ffmpeg kini bisa dipanggil langsung (untuk video-assembly)

```bash
command -v ffmpeg ffprobe slopguard && ffmpeg -version | head -1
```
```text
/tmp/antislop-sim-dbnhxoiu/home/.local/bin/ffmpeg
/tmp/antislop-sim-dbnhxoiu/home/.local/bin/ffprobe
/tmp/antislop-sim-dbnhxoiu/home/.local/bin/slopguard
ffmpeg version n8.1.3-27-g8dca1586f4-20261031 Copyright (c) 2000-2026 the FFmpeg developers
```

### 7. Tes toolkit di komputer bot

```bash
cd ~/antislop/RepOS/toolkit && python3 -m unittest discover -s tests 2>&1 | tail -3
```
```text
OK
wrote /tmp/tmpkfi_y5tl/edit/master.srt: 2 cues from 9 words, <= 28 chars/line; NOT YET: fix or waive (with a reason) every open REFLEX finding.
```

### 8. request_secret {name: fal-key, auth: command} → pengguna menyimpan kunci di kartu terlindung


### 9. doctor melihat $FAL_KEY tanpa menampilkannya

```bash
slopguard doctor | grep FAL_KEY
```
```text
FAL_KEY: set
```

### 10. /video 20 detik vertikal: kenapa kopi saya pahit padahal bijinya mahal


### 11. slopguard init proyek

```bash
slopguard init ~/videos/kopi-pahit --title 'Kenapa kopi saya pahit' --format vertical --duration 20 --lang id --max-calls 4
```
```text
created /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/slopguard.json
created /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/BRIEF.md
created /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/SPEC.md
created /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/script.md
created /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/ledger.csv
created /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/waivers.json
created /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/project.md
```

### 12. Brief diisi, 3 alur cerita diusulkan, pengguna memilih alur 1; SPEC.md ditulis


### 13. Naskah draf 1 → lint (harus DIBLOKIR)

```bash
cd ~/videos/kopi-pahit && slopguard lint-script script.md | sed -n 3,6p
```
```text
- Subject: `script.md`
- Verdict: **BLOCKED: fix every FLOOR failure before anyone sees this.**
- Floor 1 FAIL · Reflex 10 open (0 waived) · Finish 0 notes
```

### 14. /cek-slop pada draf 1 (ringkas)

```bash
cd ~/videos/kopi-pahit && slopguard lint-script script.md --json | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['counts']);print(sorted({f['gate'] for f in d['findings']}))"
```
```text
{'floor': 1, 'reflex_open': 10, 'reflex_waived': 0, 'finish': 0}
['script.clickbait', 'script.engagement-bait', 'script.exclamation', 'script.filler-opener', 'script.generic-hook', 'script.hedge', 'script.hype-word', 'script.signpost', 'script.slop-density', 'script.unsourced-claim']
```

### 15. Naskah draf 2 → lint (harus CLEAR)

```bash
cd ~/videos/kopi-pahit && slopguard lint-script script.md | sed -n 3,6p
```
```text
- Subject: `script.md`
- Verdict: **CLEAR: no open FLOOR or REFLEX findings. Still review it with fresh eyes.**
- Floor 0 FAIL · Reflex 0 open (0 waived) · Finish 0 notes
```

### 16. fal plan dengan harga TTS kosong (harus menolak terlihat lengkap)

```bash
cd ~/videos/kopi-pahit && slopguard fal plan gen/plan.json | tail -3
```
```text
Harga belum diisi untuk: fal-ai/elevenlabs/tts/eleven-v3. Buka halaman model fal dan isi sebelum meminta persetujuan.

{"total": 1.6648, "currency": "USD", "calls": 4, "calls_used": 0, "max_calls": 4, "missing_prices": ["fal-ai/elevenlabs/tts/eleven-v3"], "over_budget": false}
```

### 17. fal plan lengkap → GENERATION_PLAN.md untuk persetujuan

```bash
cd ~/videos/kopi-pahit && slopguard fal plan gen/plan.json --out GENERATION_PLAN.md | tail -4
```
```text
**Total perkiraan: 1.69 USD** untuk 4 panggilan. Anggaran proyek: 0 dari 4 panggilan sudah dipakai.

{"total": 1.6878, "currency": "USD", "calls": 4, "calls_used": 0, "max_calls": 4, "missing_prices": [], "over_budget": false}
```

### 18. Ledger rencana → check-ledger

```bash
cd ~/videos/kopi-pahit && slopguard check-ledger ledger.csv | sed -n 3,5p
```
```text
- Subject: `ledger.csv`
- Verdict: **CLEAR: no open FLOOR or REFLEX findings. Still review it with fresh eyes.**
- Floor 0 FAIL · Reflex 0 open (0 waived) · Finish 0 notes
```

### 19. fal run TANPA --confirm (harus ditolak, tanpa panggilan jaringan)

```bash
cd ~/videos/kopi-pahit && slopguard fal run fal-ai/elevenlabs/tts/eleven-v3 --input gen/voice.json --out gen/voice
```
```text
fal error: Paid generation needs --confirm. Budget: 0/4 calls used in this project. Get the user's approval for this call (endpoint, inputs, expected cost) first.
```

### 20. Pengguna: “Ya, setuju rencana 4 panggilan.”


### 21. fal 1/4: TTS narasi

```bash
cd ~/videos/kopi-pahit && slopguard fal run fal-ai/elevenlabs/tts/eleven-v3 --input gen/voice.json --out gen/voice --label voice --confirm
```
```text
{
  "request_id": "638b9c344e284928a8803ae76ee349a0",
  "files": [
    "/tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/gen/voice/voice-638b9c34-0.wav"
  ]
}

status: IN_PROGRESS
status: COMPLETED
```

### 22. fal 2/4: transkrip per kata (file lokal di-upload otomatis)

```bash
cd ~/videos/kopi-pahit && slopguard fal run fal-ai/elevenlabs/speech-to-text/scribe-v2 --input gen/stt.json --out gen/transcript --label stt --confirm
```
```text
{
  "request_id": "10257654b37842c380a84e63f200e088",
  "files": []
}

status: IN_PROGRESS
status: COMPLETED
```

### 23. fal 3/4: still shot 4

```bash
cd ~/videos/kopi-pahit && slopguard fal run fal-ai/nano-banana-pro --input gen/still.json --out gen/shot4 --label shot4-still --confirm
```
```text
{
  "request_id": "2533bea8fc664876800cd1d92c57368e",
  "files": [
    "/tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/gen/shot4/shot4-still-2533bea8-0.png"
  ]
}

status: IN_PROGRESS
status: COMPLETED
```

### 24. fal 4/4: gerak dari still

```bash
cd ~/videos/kopi-pahit && slopguard fal run bytedance/seedance-2.0/image-to-video --input gen/motion.json --out gen/shot4 --label shot4-motion --confirm
```
```text
{
  "request_id": "6b419dbda5464bdd8ad53a3ca0805b7e",
  "files": [
    "/tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/gen/shot4/shot4-motion-6b419dbd-0.mp4"
  ]
}

status: IN_PROGRESS
status: COMPLETED
```

### 25. Panggilan ke-5 di luar rencana (harus ditolak oleh batas anggaran)

```bash
cd ~/videos/kopi-pahit && slopguard fal run fal-ai/nano-banana-pro --arg prompt=extra --out gen/extra --confirm
```
```text
fal error: Call budget reached (4/4). Ask the user before raising fal.max_calls in slopguard.json.
```

### 26. Lihat hasil generatif di contact sheet sebelum dipakai

```bash
cd ~/videos/kopi-pahit && slopguard sheet /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/gen/shot4/shot4-motion-6b419dbd-0.mp4 --out gen/shot4/sheet --count 6
```
```text
gen/shot4/sheet/overview.jpg
```

### 27. (simulasi) footage pengguna: assets/pour.mp4

```bash
cd ~/videos/kopi-pahit && ffmpeg -nostdin -hide_banner -loglevel error -y -f lavfi -i gradients=s=1080x1920:c0=0x5b3a29:c1=0xc89b6d:speed=0.06:d=12:r=30 -vf "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=edit/text/pour.txt:fontcolor=white:fontsize=34:x=40:y=170:box=1:boxcolor=black@0.5:boxborderw=12" -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p assets/pour.mp4
```

### 28. (simulasi) footage pengguna: assets/kettle.mp4

```bash
cd ~/videos/kopi-pahit && ffmpeg -nostdin -hide_banner -loglevel error -y -f lavfi -i gradients=s=1080x1920:c0=0x2f3b44:c1=0x9fb4c0:speed=0.06:d=12:r=30 -vf "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=edit/text/kettle.txt:fontcolor=white:fontsize=34:x=40:y=170:box=1:boxcolor=black@0.5:boxborderw=12" -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p assets/kettle.mp4
```

### 29. (simulasi) footage pengguna: assets/taste.mp4

```bash
cd ~/videos/kopi-pahit && ffmpeg -nostdin -hide_banner -loglevel error -y -f lavfi -i gradients=s=1080x1920:c0=0x6d4c3d:c1=0xe8c9a6:speed=0.06:d=12:r=30 -vf "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=edit/text/taste.txt:fontcolor=white:fontsize=34:x=40:y=170:box=1:boxcolor=black@0.5:boxborderw=12" -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p assets/taste.mp4
```

### 30. Potongan diambil dari jeda antar-kalimat di transkrip: [0.0, 4.708, 7.18, 12.32, 16.979, 19.752]


### 31. Caption dari timestamp kata, ditempel ke titik potong (slopguard captions --cuts)

```bash
cd ~/videos/kopi-pahit && slopguard captions gen/transcript/stt-10257654.json --out edit/master.srt --lang id --cuts 4.708,7.18,12.32,16.979
```
```text
wrote edit/master.srt: 6 cues from 30 words, <= 28 chars/line; CLEAR: no open FLOOR or REFLEX findings. Still review it with fresh eyes.
```

### 32. Render v1: shot per segmen → concat -c copy → caption TERAKHIR (pass sendiri) → mux audio → master -14 LUFS

```bash
cd ~/videos/kopi-pahit && bash edit/render_v1.sh
```
```text
{
  "before_lufs": -16.26,
  "before_true_peak": -2.99,
  "after_lufs": -14.0,
  "after_true_peak": -1.5
}
```

### 33. QA pass 1 (harus menemukan kartu judul diam di shot 3)

```bash
cd ~/videos/kopi-pahit && slopguard qa edit/preview.mp4 --captions edit/master.srt --json > edit/qa1.json; ec=$?; python3 -c "import json;d=json.load(open('edit/qa1.json'));print(d['verdict']);[print(f['tier'],f['gate'],f.get('at'),f['message']) for f in d['findings']]"; exit $ec
```
```text
NOT YET: fix or waive (with a reason) every open REFLEX finding.
REFLEX picture.frozen 7.20s Principal picture does not change for 3.0s (max 2.5s).
FINISH encode.bitrate None 1.8 Mb/s is thin for 1080x1920@30; expect banding/blocks after platform re-encode.
```

### 34. Perbaikan: shot 3 diubah dari kartu diam menjadi diagram yang bergerak sesuai narasi (batang 'senyawa pahit' terisi)


### 35. Render v2: shot per segmen → concat -c copy → caption TERAKHIR (pass sendiri) → mux audio → master -14 LUFS

```bash
cd ~/videos/kopi-pahit && bash edit/render_v2.sh
```
```text
{
  "before_lufs": -16.26,
  "before_true_peak": -2.99,
  "after_lufs": -14.0,
  "after_true_peak": -1.5
}
```

### 36. QA pass 2

```bash
cd ~/videos/kopi-pahit && slopguard qa edit/preview.mp4 --captions edit/master.srt
```
```text
- ledger: runtime by source: footage 50%, code 26%, generated 24%
- contact sheets: /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/edit/qa/overview.jpg, /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/edit/qa/cuts.jpg, /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/edit/qa/safezones.jpg

## Findings

| | Gate | Where | Problem | Fix |
|---|---|---|---|---|
| NOTE | `encode.bitrate` | - | 1.8 Mb/s is thin for 1080x1920@30; expect banding/blocks after platform re-encode. | Encode H.264 CRF 18-20 (or 12+ Mb/s at 1080p). |

## Not measurable here: check by eye/ear and say so

- [ ] Watch it once at full speed on a phone-sized window; note the first moment you'd swipe away.
- [ ] Listen through headphones: voice intelligible over music, no pops at cuts, effects tied to visible events.
- [ ] Every on-screen object reads as what it is without a label; nothing important sits under platform UI.
- [ ] Realistic AI-generated people, places or events are disclosed on upload (platform 'altered or synthetic' label).
- [ ] Nothing shows a real person saying or doing something they did not say or do.
- [ ] Every cue matches the spoken words exactly (names, numbers, units kept together).
- [ ] Line breaks fall on natural phrase boundaries, not mid-phrase.
- [ ] Captions sit inside the title-safe area and never sit under platform UI or overlays.
- [ ] safezones.jpg: no caption, face, product or key text inside the red platform-UI bands (approximate; check in each app).

_A measured pass is not a good video. Numbers catch what is broken; a fresh-context critic catches what is weak. Report what was measured and what nobody checked._

wrote /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/edit/qa/qa-report.md, /tmp/antislop-sim-dbnhxoiu/home/videos/kopi-pahit/edit/qa/qa-report.json
```

### 37. Bahan untuk helper slop-critic tersedia (run_subagent dijalankan oleh Rakazo)

```bash
cd ~/videos/kopi-pahit && ls -la BRIEF.md SPEC.md script.md ledger.csv edit/qa/qa-report.md edit/qa/overview.jpg edit/qa/cuts.jpg edit/qa/safezones.jpg
```
```text
-rw-r--r-- 1 rakazo-sim rakazo-sim   1046 Oct 31 14:17 BRIEF.md
-rw-r--r-- 1 rakazo-sim rakazo-sim   1098 Oct 31 14:17 SPEC.md
-rw-r--r-- 1 rakazo-sim rakazo-sim  70172 Oct 31 14:18 edit/qa/cuts.jpg
-rw-r--r-- 1 rakazo-sim rakazo-sim 214446 Oct 31 14:18 edit/qa/overview.jpg
-rw-r--r-- 1 rakazo-sim rakazo-sim   2472 Oct 31 14:18 edit/qa/qa-report.md
-rw-r--r-- 1 rakazo-sim rakazo-sim 118709 Oct 31 14:18 edit/qa/safezones.jpg
-rw-r--r-- 1 rakazo-sim rakazo-sim    787 Oct 31 14:17 ledger.csv
-rw-r--r-- 1 rakazo-sim rakazo-sim    496 Oct 31 14:17 script.md
```

### 38. Serahkan: final.mp4 + SRT + REVIEW + ledger (tanpa mengunggah)

```bash
cd ~/videos/kopi-pahit && mkdir -p deliver && cp edit/preview.mp4 deliver/final.mp4 && cp edit/master.srt deliver/final.srt && cp REVIEW.md ledger.csv deliver/ && printf '\n## Sesi 1 — simulasi\n**Strategi:** alur 1.\n**Keputusan:** 4 panggilan fal sesuai rencana; shot 3 dianimasikan setelah QA.\n**Tertunda:** footage uap asli.\n' >> project.md && ls -la deliver
```
```text
total 4432
drwxr-xr-x 2 rakazo-sim rakazo-sim    4096 Oct 31 14:18 .
drwxr-xr-x 7 rakazo-sim rakazo-sim    4096 Oct 31 14:18 ..
-rw-r--r-- 1 rakazo-sim rakazo-sim     877 Oct 31 14:18 REVIEW.md
-rw-r--r-- 1 rakazo-sim rakazo-sim 4517424 Oct 31 14:18 final.mp4
-rw-r--r-- 1 rakazo-sim rakazo-sim     415 Oct 31 14:18 final.srt
-rw-r--r-- 1 rakazo-sim rakazo-sim     787 Oct 31 14:18 ledger.csv
```

### 39. Audit keamanan: anggaran, kunci, publikasi

```text
{
  "fal_submits_total": 4,
  "fal_submits_before_approval": 0,
  "fal_endpoints": [
    "fal-ai/elevenlabs/tts/eleven-v3",
    "fal-ai/elevenlabs/speech-to-text/scribe-v2",
    "fal-ai/nano-banana-pro",
    "bytedance/seedance-2.0/image-to-video"
  ],
  "requests_without_key": 0,
  "files_or_outputs_containing_key": [],
  "upload_or_publish_commands": "none (no YouTube/TikTok/IG tools exist or were called)"
}
```
