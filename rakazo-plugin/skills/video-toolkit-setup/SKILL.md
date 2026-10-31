---
name: video-toolkit-setup
description: Install or repair the anti-slop video toolkit on the bot's computer (slopguard CLI, static ffmpeg and ffprobe) and connect the fal.ai key safely. Use on first use, when slopguard doctor fails, when ffmpeg is missing, or when the user wants to set up fal.ai or FAL_KEY.
---

# Toolkit setup

The bot computer runs as a normal user with no package manager, but it has `git`, `curl`, `python3`
and `uv`. Everything installs into the home folder.

## Install or update

```bash
if [ -d ~/antislop/RepOS/.git ]; then git -C ~/antislop/RepOS pull --ff-only; \
else mkdir -p ~/antislop && git clone --depth 1 https://github.com/Jeaniro07/RepOS ~/antislop/RepOS; fi
bash ~/antislop/RepOS/toolkit/setup.sh
slopguard doctor
```

`setup.sh` downloads a static ffmpeg + ffprobe build (about 150 MB, BtbN/FFmpeg-Builds) into
`~/.local/share/slopguard/bin` when none is installed, falls back to the imageio-ffmpeg wheel through `uv`,
and puts a `slopguard` command in `~/.local/bin`. It never reads or writes secrets. `doctor` must show
ffmpeg found and "filters: all present".

Run the toolkit's own tests once after a fresh install if you want proof it works on this computer:

```bash
cd ~/antislop/RepOS/toolkit && python3 -m unittest discover -s tests
```

## fal.ai key

Ask for it with a protected card, never in chat:

```json
{"label": "fal.ai API key", "purpose": "api_key", "credential": {"name": "fal-key", "auth": {"type": "command"}}}
```

After the user saves it, `$FAL_KEY` is exported to your shell commands. `slopguard doctor` should then show
`FAL_KEY: set`. Never echo, print, log, or write the key to a file. If the user prefers the fal MCP connector,
point them to Integrations → Manage MCP servers → fal → Advanced → Access token, then **Use in this bot**.

## Optional tools, only when a video needs them

- Node.js 22+ for HyperFrames or Remotion (check `node --version` first).
- `uv tool install yt-dlp` to download the user's own online footage they have rights to.
- Manim through `uv` in a project-local environment for diagram-heavy explainers.

Tell the user what you installed and why, in one line each.
