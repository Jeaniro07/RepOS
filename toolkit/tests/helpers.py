"""Synthetic test media built with ffmpeg's lavfi sources."""

from __future__ import annotations

import os
import shutil
import subprocess

FFMPEG = shutil.which("ffmpeg")


def _run(args):
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y"] + args, check=True)


def make_sloppy(path: str, size: str = "540x960") -> str:
    """1.5 s black, 5 s frozen flat card, 8 s motion; audio clips and has a 4 s hole."""
    _run(
        [
            "-f", "lavfi", "-i", f"color=c=black:s={size}:r=30:d=1.5",
            "-f", "lavfi", "-i", f"color=c=0x4682b4:s={size}:r=30:d=5",
            "-f", "lavfi", "-i", f"testsrc2=s={size}:r=30:d=8",
            "-f", "lavfi", "-i", "aevalsrc=0.999*sin(2*PI*440*t)*(lt(t\\,6)+gt(t\\,10)):s=48000:d=14.5",
            "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]",
            "-map", "[v]", "-map", "3:a", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", path,
        ]
    )
    return path


def make_clean(path: str, size: str = "540x960") -> str:
    """Moving picture with irregular cuts, steady audio normalised near -14 LUFS."""
    durs = [3.3, 1.9, 4.6, 2.4, 3.8]
    srcs = [
        f"testsrc2=s={size}:r=30:d={durs[0]}",
        f"mandelbrot=s={size}:r=30,trim=duration={durs[1]}",
        f"testsrc=s={size}:r=30:d={durs[2]},hue=h=t*40",
        f"life=s={size}:r=30:mold=10:ratio=0.2:death_color=#c83232:life_color=#00ff88,trim=duration={durs[3]}",
        f"rgbtestsrc=s={size}:r=30:d={durs[4]},rotate=a=t:fillcolor=0x202020",
    ]
    args = []
    for s in srcs:
        args += ["-f", "lavfi", "-i", s]
    total = sum(durs)
    args += ["-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.25:d={total}:r=48000"]
    chains = "".join(f"[{i}:v]scale={size},setsar=1,fps=30,format=yuv420p[v{i}];" for i in range(len(srcs)))
    concat = "".join(f"[v{i}]" for i in range(len(srcs))) + f"concat=n={len(srcs)}:v=1:a=0[v];"
    audio = f"[{len(srcs)}:a]lowpass=f=3500,loudnorm=I=-14:TP=-2:LRA=7[a]"
    _run(
        args
        + [
            "-filter_complex", chains + concat + audio,
            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{total}", path,
        ]
    )
    return path


def make_metronomic(path: str, size: str = "540x960", shots: int = 8, shot_len: float = 2.0) -> str:
    """Alternating sources cut on an exact timer."""
    args = []
    for i in range(shots):
        src = "testsrc2" if i % 2 == 0 else "testsrc"
        args += ["-f", "lavfi", "-i", f"{src}=s={size}:r=30:d={shot_len},hue=h={i * 45}"]
    total = shots * shot_len
    args += ["-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.25:d={total}:r=48000"]
    chains = "".join(f"[{i}:v]format=yuv420p[v{i}];" for i in range(shots))
    concat = "".join(f"[v{i}]" for i in range(shots)) + f"concat=n={shots}:v=1:a=0[v];"
    audio = f"[{shots}:a]loudnorm=I=-14:TP=-2[a]"
    _run(args + ["-filter_complex", chains + concat + audio, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", path])
    return path


def have_ffmpeg() -> bool:
    return FFMPEG is not None and os.access(FFMPEG, os.X_OK)
