"""Contact sheets for review: the agent (and a fresh-context critic) looks at
a handful of PNGs instead of the whole video.

  overview.jpg   N evenly spaced frames, tiled
  cuts.jpg       a frame just before and just after every detected cut
"""

from __future__ import annotations

import math
import os
import shutil
import tempfile
from typing import List, Optional

from slopguard import media


def _tile(frames: List[str], out: str, cols: int) -> bool:
    if not frames:
        return False
    tmp = tempfile.mkdtemp(prefix="slopguard-tile-")
    try:
        for i, f in enumerate(frames):
            shutil.copy(f, os.path.join(tmp, f"f{i:04d}.jpg"))
        rows = math.ceil(len(frames) / cols)
        cmd = [
            media.ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-y", "-framerate", "1",
            "-i", os.path.join(tmp, "f%04d.jpg"),
            "-vf", f"tile={cols}x{rows}:padding=6:margin=6:color=white", "-frames:v", "1", out,
        ]
        code, _, _ = media.run(cmd, timeout=300)
        return code == 0 and os.path.exists(out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def overview(path: str, out_dir: str, count: int = 20, width: int = 360, duration: Optional[float] = None) -> Optional[str]:
    duration = duration or media.probe(path).duration
    os.makedirs(out_dir, exist_ok=True)
    frames_dir = os.path.join(out_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    frames = []
    for i in range(count):
        t = (i + 0.5) * duration / count
        f = os.path.join(frames_dir, f"t{t:08.2f}.jpg")
        if media.extract_frame(path, t, f, width=width):
            frames.append(f)
    out = os.path.join(out_dir, "overview.jpg")
    return out if _tile(frames, out, cols=5) else None


def cut_strip(path: str, cuts: List[float], out_dir: str, width: int = 320, pad: float = 0.2, limit: int = 24) -> Optional[str]:
    if not cuts:
        return None
    os.makedirs(out_dir, exist_ok=True)
    frames_dir = os.path.join(out_dir, "cut-frames")
    os.makedirs(frames_dir, exist_ok=True)
    frames = []
    for c in cuts[:limit]:
        for t, tag in ((c - pad, "a"), (c + pad, "b")):
            f = os.path.join(frames_dir, f"cut{c:08.2f}{tag}.jpg")
            if media.extract_frame(path, t, f, width=width):
                frames.append(f)
    out = os.path.join(out_dir, "cuts.jpg")
    return out if _tile(frames, out, cols=4) else None


# Approximate platform UI bands on a 1080x1920 frame (TikTok / Reels / Shorts differ and change;
# vendor guides give top 120-200, bottom 250-370, right 120-164, left 50-60 px). The green box is
# the conservative shared area (about 900x1400, centred) where text, faces and products belong.
SAFE_BANDS = {"top": 200, "bottom": 370, "right": 164, "left": 60}
SAFE_BOX = (900, 1400)


def safe_zone_sheet(path: str, out_dir: str, duration: float, count: int = 5, width: int = 360) -> Optional[str]:
    """Frames with the platform UI bands shaded, to check captions and key content by eye."""
    os.makedirs(out_dir, exist_ok=True)
    frames_dir = os.path.join(out_dir, "safe-frames")
    os.makedirs(frames_dir, exist_ok=True)
    frames = []
    for i in range(count):
        t = (i + 0.5) * duration / count
        f = os.path.join(frames_dir, f"t{t:08.2f}.png")
        if media.extract_frame(path, t, f, width=width):
            frames.append(f)
    if not frames:
        return None
    b = SAFE_BANDS
    bw, bh = SAFE_BOX
    shade = "color=red@0.35:t=fill"
    vf = ",".join([
        f"drawbox=x=0:y=0:w=iw:h=ih*{b['top']}/1920:{shade}",
        f"drawbox=x=0:y=ih-ih*{b['bottom']}/1920:w=iw:h=ih*{b['bottom']}/1920:{shade}",
        f"drawbox=x=iw-iw*{b['right']}/1080:y=ih*{b['top']}/1920:w=iw*{b['right']}/1080:h=ih-ih*{b['top'] + b['bottom']}/1920:{shade}",
        f"drawbox=x=0:y=ih*{b['top']}/1920:w=iw*{b['left']}/1080:h=ih-ih*{b['top'] + b['bottom']}/1920:{shade}",
        f"drawbox=x=(iw-iw*{bw}/1080)/2:y=(ih-ih*{bh}/1920)/2:w=iw*{bw}/1080:h=ih*{bh}/1920:color=lime@0.9:t=3",
    ])
    tmp = tempfile.mkdtemp(prefix="slopguard-safe-")
    try:
        for i, f in enumerate(frames):
            shutil.copy(f, os.path.join(tmp, f"f{i:04d}.png"))
        out = os.path.join(out_dir, "safezones.jpg")
        cmd = [
            media.ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-y", "-framerate", "1",
            "-i", os.path.join(tmp, "f%04d.png"), "-vf", vf + f",tile={len(frames)}x1:padding=6:margin=6:color=white",
            "-frames:v", "1", out,
        ]
        code, _, _ = media.run(cmd, timeout=300)
        return out if code == 0 and os.path.exists(out) else None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
