# Simulasi: bot Rakazo memakai plugin antislop-video

- Tanggal: 2026-10-31 13:10 UTC
- Repo yang di-clone bot: `https://github.com/Jeaniro07/RepOS` ref `claude/keen-einstein-1e7dc9`
- Hasil: **18/20 langkah sesuai harapan**
- Skill terpasang menurut parser Rakazo: 

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
| 14 | bot | cek-slop (command) | /cek-slop pada draf 1 (ringkas) | 1 (0) | ❌ |
| 15 | bot | antislop-script | Naskah draf 2 → lint (harus CLEAR) | 0 (0) | ✅ |
| 16 | bot | antislop-video-director | Ledger rencana → check-ledger | 0 (0) | ✅ |
| 17 | bot | fal-media | fal run TANPA --confirm (harus ditolak, tanpa panggilan jaringan) | 3 (3) | ✅ |
| 18 | user | fal-media | Pengguna: “Ya, setuju rencana 4 panggilan.” | - | ✅ |
| 19 | bot | fal-media | fal 1/4: TTS narasi | 0 (0) | ✅ |
| 20 | bot | fal-media | fal 2/4: transkrip per kata (file lokal di-upload otomatis) | 3 (0) | ❌ |

## Audit

```json
{}
```

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
/home/user/RepOS/rakazo-plugin: 17 files, 47142 bytes, 7 skills/agents
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
downloading https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz (about 150 MB)...
installed /tmp/antislop-sim-_ivzqubi/home/.local/share/slopguard/bin/ffmpeg
installed /tmp/antislop-sim-_ivzqubi/home/.local/share/slopguard/bin/ffprobe
slopguard 0.1.0  python 3.11.18
ffmpeg : /tmp/antislop-sim-_ivzqubi/home/.local/bin/ffmpeg
ffprobe: /tmp/antislop-sim-_ivzqubi/home/.local/bin/ffprobe
FAL_KEY: not set (needed only for fal generation)
filters: all present
slopguard 0.1.0  python 3.11.18
ffmpeg : /tmp/antislop-sim-_ivzqubi/home/.local/bin/ffmpeg
ffprobe: /tmp/antislop-sim-_ivzqubi/home/.local/bin/ffprobe
FAL_KEY: not set (needed only for fal generation)
filters: all present

Cloning into '/tmp/antislop-sim-_ivzqubi/home/antislop/RepOS'...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed

  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0

 10  150M   10 16.0M    0     0  17.2M      0  0:00:08 --:--:--  0:00:08 17.2M
 27  150M   27 40.8M    0     0  21.0M      0  0:00:07  0:00:01  0:00:06 24.5M
 43  150M   43 64.6M    0     0  21.8M      0  0:00:06  0:00:02  0:00:04 23.9M
 58  150M   58 88.5M    0     0  22.4M      0  0:00:06  0:00:03  0:00:03 24.0M
 75  150M   75  112M    0     0  22.8M      0  0:00:06  0:00:04  0:00:02 24.1M
 91  150M   91  137M    0     0  23.1M      0  0:00:06  0:00:05  0:00:01 24.2M
100  150M  100  150M    0     0  23.2M      0  0:00:06  0:00:06 --:--:-- 24.1M
```

### 6. ffmpeg kini bisa dipanggil langsung (untuk video-assembly)

```bash
command -v ffmpeg ffprobe slopguard && ffmpeg -version | head -1
```
```text
/tmp/antislop-sim-_ivzqubi/home/.local/bin/ffmpeg
/tmp/antislop-sim-_ivzqubi/home/.local/bin/ffprobe
/tmp/antislop-sim-_ivzqubi/home/.local/bin/slopguard
ffmpeg version N-128212-g17a4a474f4-20261030 Copyright (c) 2000-2026 the FFmpeg developers
```

### 7. Tes toolkit di komputer bot

```bash
cd ~/antislop/RepOS/toolkit && python3 -m unittest discover -s tests 2>&1 | tail -3
```
```text
Ran 24 tests in 10.454s

OK
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
created /tmp/antislop-sim-_ivzqubi/home/videos/kopi-pahit/slopguard.json
created /tmp/antislop-sim-_ivzqubi/home/videos/kopi-pahit/BRIEF.md
created /tmp/antislop-sim-_ivzqubi/home/videos/kopi-pahit/SPEC.md
created /tmp/antislop-sim-_ivzqubi/home/videos/kopi-pahit/script.md
created /tmp/antislop-sim-_ivzqubi/home/videos/kopi-pahit/ledger.csv
created /tmp/antislop-sim-_ivzqubi/home/videos/kopi-pahit/waivers.json
created /tmp/antislop-sim-_ivzqubi/home/videos/kopi-pahit/project.md
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

### 16. Ledger rencana → check-ledger

```bash
cd ~/videos/kopi-pahit && slopguard check-ledger ledger.csv | sed -n 3,5p
```
```text
- Subject: `ledger.csv`
- Verdict: **CLEAR: no open FLOOR or REFLEX findings. Still review it with fresh eyes.**
- Floor 0 FAIL · Reflex 0 open (0 waived) · Finish 0 notes
```

### 17. fal run TANPA --confirm (harus ditolak, tanpa panggilan jaringan)

```bash
cd ~/videos/kopi-pahit && slopguard fal run fal-ai/elevenlabs/tts/eleven-v3 --input gen/voice.json --out gen/voice
```
```text
fal error: Paid generation needs --confirm. Budget: 0/4 calls used in this project. Get the user's approval for this call (endpoint, inputs, expected cost) first.
```

### 18. Pengguna: “Ya, setuju rencana 4 panggilan.”


### 19. fal 1/4: TTS narasi

```bash
cd ~/videos/kopi-pahit && slopguard fal run fal-ai/elevenlabs/tts/eleven-v3 --input gen/voice.json --out gen/voice --label voice --confirm
```
```text
{
  "request_id": "1aaadb4a4f5b4f1cbb480fa006170f96",
  "files": [
    "gen/voice/voice-1aaadb4a-0.wav"
  ]
}

status: IN_PROGRESS
status: COMPLETED
```

### 20. fal 2/4: transkrip per kata (file lokal di-upload otomatis)

```bash
cd ~/videos/kopi-pahit && slopguard fal run fal-ai/elevenlabs/speech-to-text/scribe-v2 --input gen/stt.json --out gen/transcript --label stt --confirm
```
```text
fal error: An input *_url points at a local path that does not exist. Use a path relative to the project folder, or a URL.
```
