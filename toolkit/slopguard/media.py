"""ffmpeg / ffprobe discovery and measurement helpers.

Discovery order for each binary:
  1. $SLOPGUARD_FFMPEG / $SLOPGUARD_FFPROBE (set to "none" to disable)
  2. PATH
  3. ~/.local/share/slopguard/bin (where setup.sh puts static builds)
  4. imageio-ffmpeg's bundled ffmpeg (ffmpeg only), if importable
ffprobe is optional: without it, stream info is parsed from `ffmpeg -i`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

LOCAL_BIN = os.path.join(os.path.expanduser("~"), ".local", "share", "slopguard", "bin")


class MediaError(RuntimeError):
    pass


def _find(name: str) -> Optional[str]:
    env = os.environ.get(f"SLOPGUARD_{name.upper()}")
    if env:
        if env.lower() == "none":
            return None
        return env if os.path.exists(env) else shutil.which(env)
    found = shutil.which(name)
    if found:
        return found
    local = os.path.join(LOCAL_BIN, name)
    if os.path.exists(local):
        return local
    if name == "ffmpeg":
        try:
            import imageio_ffmpeg  # type: ignore

            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return None
    return None


def ffmpeg_path() -> str:
    path = _find("ffmpeg")
    if not path:
        raise MediaError(
            "ffmpeg not found. Run toolkit/setup.sh, or set SLOPGUARD_FFMPEG to an ffmpeg binary."
        )
    return path


def ffprobe_path() -> Optional[str]:
    return _find("ffprobe")


def run(cmd: List[str], timeout: int = 1800) -> Tuple[int, str, str]:
    """Run a media tool with no stdin. Without -nostdin, ffmpeg treats stdin as a
    keyboard; under an agent (no terminal, closed or piped stdin) it can read an
    input file's bytes as commands and hang or corrupt the read."""
    if cmd and os.path.basename(cmd[0]).startswith("ffmpeg") and "-nostdin" not in cmd:
        cmd = [cmd[0], "-nostdin"] + list(cmd[1:])
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
    return proc.returncode, proc.stdout, proc.stderr


@dataclass
class Probe:
    path: str
    duration: float
    width: int = 0
    height: int = 0
    fps: float = 0.0
    vcodec: str = ""
    has_video: bool = False
    has_audio: bool = False
    acodec: str = ""
    sample_rate: int = 0
    channels: int = 0
    bitrate: int = 0  # bits/s, whole file
    rotation: int = 0
    extra: Dict[str, str] = field(default_factory=dict)

    @property
    def display_size(self) -> Tuple[int, int]:
        if self.rotation in (90, 270, -90):
            return self.height, self.width
        return self.width, self.height


def probe(path: str) -> Probe:
    if not os.path.exists(path):
        raise MediaError(f"File not found: {path}")
    fp = ffprobe_path()
    if fp:
        code, out, err = run(
            [fp, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path], timeout=120
        )
        if code == 0:
            return _probe_from_json(path, json.loads(out or "{}"))
    return _probe_from_ffmpeg(path)


def _rate(value: str) -> float:
    try:
        if "/" in value:
            a, b = value.split("/")
            return float(a) / float(b) if float(b) else 0.0
        return float(value)
    except (ValueError, ZeroDivisionError):
        return 0.0


def _probe_from_json(path: str, data: dict) -> Probe:
    fmt = data.get("format", {})
    p = Probe(path=path, duration=float(fmt.get("duration") or 0.0), bitrate=int(fmt.get("bit_rate") or 0))
    for s in data.get("streams", []):
        if s.get("codec_type") == "video" and not p.has_video:
            disposition = s.get("disposition", {}) or {}
            if disposition.get("attached_pic"):
                continue
            p.has_video = True
            p.width, p.height = int(s.get("width") or 0), int(s.get("height") or 0)
            p.fps = _rate(s.get("avg_frame_rate") or "0") or _rate(s.get("r_frame_rate") or "0")
            p.vcodec = s.get("codec_name", "")
            rot = (s.get("tags", {}) or {}).get("rotate")
            for side in s.get("side_data_list", []) or []:
                if "rotation" in side:
                    rot = side["rotation"]
            p.rotation = abs(int(float(rot))) % 360 if rot not in (None, "") else 0
            if not p.duration and s.get("duration"):
                p.duration = float(s["duration"])
        elif s.get("codec_type") == "audio" and not p.has_audio:
            p.has_audio = True
            p.acodec = s.get("codec_name", "")
            p.sample_rate = int(s.get("sample_rate") or 0)
            p.channels = int(s.get("channels") or 0)
    return p


_DUR_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_BR_RE = re.compile(r"bitrate:\s*(\d+)\s*kb/s")
_VID_RE = re.compile(r"Stream #\S+.*?Video:\s*(\w+).*?(\d{2,5})x(\d{2,5})")
_FPS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*fps")
_AUD_RE = re.compile(r"Stream #\S+.*?Audio:\s*(\w+).*?(\d+)\s*Hz")


def _probe_from_ffmpeg(path: str) -> Probe:
    code, _, err = run([ffmpeg_path(), "-hide_banner", "-i", path], timeout=120)
    m = _DUR_RE.search(err)
    if not m:
        raise MediaError(f"Could not read {path}: {err.strip().splitlines()[-1] if err.strip() else 'unknown error'}")
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    p = Probe(path=path, duration=dur)
    br = _BR_RE.search(err)
    if br:
        p.bitrate = int(br.group(1)) * 1000
    for line in err.splitlines():
        if "Video:" in line and not p.has_video and "attached pic" not in line:
            vm = _VID_RE.search(line)
            if vm:
                p.has_video = True
                p.vcodec, p.width, p.height = vm.group(1), int(vm.group(2)), int(vm.group(3))
                fm = _FPS_RE.search(line)
                p.fps = float(fm.group(1)) if fm else 0.0
        elif "Audio:" in line and not p.has_audio:
            am = _AUD_RE.search(line)
            p.has_audio = True
            if am:
                p.acodec, p.sample_rate = am.group(1), int(am.group(2))
        elif "rotate" in line and ":" in line:
            try:
                p.rotation = abs(int(float(line.split(":")[-1].strip()))) % 360
            except ValueError:
                pass
        elif "displaymatrix: rotation of" in line:
            mm = re.search(r"rotation of (-?\d+(?:\.\d+)?)", line)
            if mm:
                p.rotation = abs(int(float(mm.group(1)))) % 360
    return p


# ---------------------------------------------------------------- audio


@dataclass
class AudioStats:
    integrated_lufs: Optional[float] = None
    loudness_range: Optional[float] = None
    true_peak_dbtp: Optional[float] = None
    silences: List[Tuple[float, float]] = field(default_factory=list)  # (start, end)


def audio_stats(path: str, silence_db: float = -45.0, silence_min: float = 1.2) -> AudioStats:
    cmd = [
        ffmpeg_path(), "-hide_banner", "-nostats", "-i", path, "-vn",
        "-af", f"silencedetect=noise={silence_db}dB:d={silence_min},ebur128=peak=true:framelog=verbose",
        "-f", "null", "-",
    ]
    code, _, err = run(cmd)
    st = AudioStats()
    summary = err[err.rfind("Summary:"):] if "Summary:" in err else ""
    m = re.search(r"I:\s*(-?\d+(?:\.\d+)?|-inf)\s*LUFS", summary)
    if m and m.group(1) != "-inf":
        st.integrated_lufs = float(m.group(1))
    m = re.search(r"LRA:\s*(-?\d+(?:\.\d+)?)\s*LU", summary)
    if m:
        st.loudness_range = float(m.group(1))
    m = re.search(r"True peak:\s*Peak:\s*(-?\d+(?:\.\d+)?|-inf)\s*dBFS", summary)
    if m and m.group(1) != "-inf":
        st.true_peak_dbtp = float(m.group(1))
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?\d+(?:\.\d+)?)", err)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*(-?\d+(?:\.\d+)?)", err)]
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        st.silences.append((max(0.0, s), e if e is not None else -1.0))
    return st


# ---------------------------------------------------------------- picture


@dataclass
class PictureStats:
    blacks: List[Tuple[float, float]] = field(default_factory=list)
    freezes: List[Tuple[float, float]] = field(default_factory=list)
    cuts: List[float] = field(default_factory=list)
    first_frame_luma: Optional[float] = None
    first_frame_range: Optional[float] = None


def picture_stats(
    path: str,
    duration: float,
    scene_threshold: float = 0.30,
    freeze_min: float = 2.5,
    freeze_noise_db: float = -55.0,
    principal_region: bool = True,
) -> PictureStats:
    """One decoding pass: black segments, frozen principal picture, cuts.

    principal_region crops away the top 8% and bottom 22% (platform UI and
    the caption band) so changing captions cannot hide a frozen picture.
    """
    chain = []
    if principal_region:
        chain.append("crop=iw:ih*0.70:0:ih*0.08")
    chain += [
        "scale=320:-2",
        "blackdetect=d=0.4:pix_th=0.10",
        f"freezedetect=n={freeze_noise_db}dB:d={freeze_min}",
        f"select='gt(scene\\,{scene_threshold})'",
        "showinfo",
    ]
    cmd = [ffmpeg_path(), "-hide_banner", "-nostats", "-i", path, "-an", "-vf", ",".join(chain), "-f", "null", "-"]
    code, _, err = run(cmd)
    st = PictureStats()
    for m in re.finditer(r"black_start:\s*(\d+(?:\.\d+)?)\s+black_end:\s*(\d+(?:\.\d+)?)", err):
        st.blacks.append((float(m.group(1)), float(m.group(2))))
    fstarts = [float(x) for x in re.findall(r"freeze_start:\s*(\d+(?:\.\d+)?)", err)]
    fends = [float(x) for x in re.findall(r"freeze_end:\s*(\d+(?:\.\d+)?)", err)]
    for i, s in enumerate(fstarts):
        e = fends[i] if i < len(fends) else duration
        st.freezes.append((s, e))
    for m in re.finditer(r"Parsed_showinfo.*?pts_time:\s*(\d+(?:\.\d+)?)", err):
        st.cuts.append(float(m.group(1)))
    lum = first_frame_signal(path)
    if lum:
        st.first_frame_luma, st.first_frame_range = lum
    return st


def first_frame_signal(path: str) -> Optional[Tuple[float, float]]:
    cmd = [
        ffmpeg_path(), "-hide_banner", "-nostats", "-i", path, "-an", "-frames:v", "1",
        "-vf", "signalstats,metadata=print", "-f", "null", "-",
    ]
    code, _, err = run(cmd, timeout=120)
    yavg = re.search(r"lavfi\.signalstats\.YAVG=(\d+(?:\.\d+)?)", err)
    ylow = re.search(r"lavfi\.signalstats\.YLOW=(\d+(?:\.\d+)?)", err)
    yhigh = re.search(r"lavfi\.signalstats\.YHIGH=(\d+(?:\.\d+)?)", err)
    if not yavg:
        return None
    rng = float(yhigh.group(1)) - float(ylow.group(1)) if (ylow and yhigh) else 255.0
    return float(yavg.group(1)), rng


def extract_frame(path: str, t: float, out: str, width: int = 480) -> bool:
    cmd = [
        ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(t, 0):.3f}", "-i", path,
        "-frames:v", "1", "-vf", f"scale={width}:-2", out,
    ]
    code, _, _ = run(cmd, timeout=120)
    return code == 0 and os.path.exists(out)
