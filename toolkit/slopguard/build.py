"""Deterministic production steps an agent should not improvise:

  captions_from_words()  word timestamps -> readable SRT on the output timeline
  master_loudness()      two-pass loudnorm to a target (default -14 LUFS, -1.5 dBTP)
"""

from __future__ import annotations

import json
import re
from typing import List, Optional, Tuple

from slopguard import media

Word = Tuple[str, float, float]  # (text, start, end)

# Words a caption line should not end on (they belong to what follows).
DANGLING = {
    "id": {"di", "ke", "dari", "yang", "dan", "atau", "untuk", "dengan", "pada", "ini", "itu", "si", "sang", "para", "tidak", "bukan", "akan", "sudah", "lebih", "paling", "se", "per"},
    "en": {"a", "an", "the", "of", "to", "in", "on", "at", "for", "and", "or", "but", "with", "from", "by", "is", "are", "not", "my", "your", "our", "their"},
}
SENTENCE_END = re.compile(r"[.!?…]$")
CLAUSE_END = re.compile(r"[,;:—-]$")


# ------------------------------------------------------------------ words


def extract_words(data) -> List[Word]:
    """Find word timings in common transcript JSON shapes:
    ElevenLabs Scribe {"words":[{"text","start","end","type"}]}, Whisper/WhisperX
    {"segments":[{"words":[{"word","start","end"}]}]}, fal wizper/whisper
    {"chunks":[{"text","timestamp":[s,e]}]}, or a plain list of such items."""
    out: List[Word] = []

    def visit(node):
        if isinstance(node, dict):
            text = node.get("text", node.get("word"))
            start, end = node.get("start"), node.get("end")
            if start is None and isinstance(node.get("timestamp"), (list, tuple)) and len(node["timestamp"]) == 2:
                start, end = node["timestamp"]
            if isinstance(text, str) and isinstance(start, (int, float)) and isinstance(end, (int, float)) and not node.get("words"):
                if node.get("type") in (None, "word") and text.strip():
                    out.append((text.strip(), float(start), float(end)))
                return
            for key in ("words", "segments", "chunks", "results", "transcription", "output"):
                if key in node:
                    visit(node[key])
                    return
            for v in node.values():
                if isinstance(v, (list, dict)):
                    visit(v)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(data)
    out.sort(key=lambda w: w[1])
    # Chunk-level input (several words per item): spread the time over the words.
    expanded: List[Word] = []
    for text, s, e in out:
        parts = text.split()
        if len(parts) <= 1:
            expanded.append((text, s, e))
            continue
        total = sum(len(p) for p in parts) or 1
        t = s
        for p in parts:
            d = (e - s) * len(p) / total
            expanded.append((p, t, t + d))
            t += d
    return expanded


def map_to_output(words: List[Word], ranges: List[dict]) -> List[Word]:
    """Keep words inside EDL ranges and shift them to the output timeline:
    output_time = word.start - range.start + range_offset."""
    out: List[Word] = []
    offset = 0.0
    for r in ranges:
        rs, re_ = float(r["start"]), float(r["end"])
        for text, s, e in words:
            if s >= rs - 0.02 and e <= re_ + 0.02:
                out.append((text, max(0.0, s - rs + offset), min(re_, e) - rs + offset))
        offset += re_ - rs
    return out


# ------------------------------------------------------------------ cues


def _split_lines(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    best, best_score = None, None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if len(a) > max_chars or len(b) > max_chars:
            continue
        score = abs(len(a) - len(b)) + (8 if words[i - 1].lower().strip(",.") in DANGLING["id"] | DANGLING["en"] else 0)
        if best_score is None or score < best_score:
            best, best_score = [a, b], score
    return best or [text]


def captions_from_words(
    words: List[Word],
    lang: str = "id",
    max_chars: int = 42,
    max_lines: int = 2,
    max_cps: float = 17.0,
    min_dur: float = 0.8,
    max_dur: float = 6.0,
    pause_break: float = 0.35,
    gap: float = 0.04,
    video_end: Optional[float] = None,
) -> List[Tuple[float, float, List[str]]]:
    dangling = DANGLING.get(lang, set()) | DANGLING["en"]
    limit = max_chars * max_lines
    cues: List[List[Word]] = []
    cur: List[Word] = []
    for i, w in enumerate(words):
        cur.append(w)
        text = " ".join(x[0] for x in cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt is None:
            break
        nxt_text = text + " " + nxt[0]
        pause = nxt[1] - w[2]
        bare = w[0].lower().strip(",.!?")
        is_number = bool(re.fullmatch(r"[\d.,%]+", bare))
        hard = SENTENCE_END.search(w[0]) is not None or pause >= pause_break * 2
        soft = CLAUSE_END.search(w[0]) is not None or pause >= pause_break
        too_long = len(nxt_text) > limit or (nxt[2] - cur[0][1]) > max_dur
        if (bare in dangling or is_number) and not hard and not too_long:
            continue  # keep "di", "92", "the" with the word that follows
        if hard or too_long or (soft and len(text) >= max_chars * 0.6):
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)

    out: List[Tuple[float, float, List[str]]] = []
    for idx, cue in enumerate(cues):
        text = " ".join(w[0] for w in cue)
        start, end = cue[0][1], cue[-1][2]
        next_start = cues[idx + 1][0][1] if idx + 1 < len(cues) else (video_end if video_end else end + 2.0)
        chars = len(text.replace(" ", ""))
        need = max(min_dur, chars / max_cps)
        end = max(end, min(start + need, next_start - gap))
        if video_end:
            end = min(end, video_end)
        out.append((start, end, _split_lines(text, max_chars)))
    return out


def _ts(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(cues) -> str:
    blocks = []
    for i, (s, e, lines) in enumerate(cues, start=1):
        blocks.append(f"{i}\n{_ts(s)} --> {_ts(e)}\n" + "\n".join(lines) + "\n")
    return "\n".join(blocks)


# ------------------------------------------------------------------ loudness


def measure_loudnorm(path: str, lufs: float, tp: float, lra: float) -> dict:
    cmd = [
        media.ffmpeg_path(), "-hide_banner", "-nostats", "-i", path, "-vn",
        "-af", f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:print_format=json", "-f", "null", "-",
    ]
    code, _, err = media.run(cmd)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S)
    if not m:
        raise media.MediaError("loudnorm measurement failed (is there an audio stream?)")
    return json.loads(m.group(0))


def master_loudness(src: str, dst: str, lufs: float = -14.0, tp: float = -1.5, lra: float = 11.0) -> dict:
    """Two-pass loudnorm. Video is stream-copied; audio re-encoded (AAC for video
    containers, PCM for .wav)."""
    m = measure_loudnorm(src, lufs, tp, lra)
    af = (
        f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
        f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}"
        ":linear=true:print_format=summary,aresample=48000"
    )
    probe = media.probe(src)
    cmd = [media.ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-y", "-i", src]
    if probe.has_video and not dst.lower().endswith(".wav"):
        cmd += ["-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst]
    else:
        cmd += ["-vn", "-af", af, dst]
    code, _, err = media.run(cmd)
    if code != 0:
        raise media.MediaError(f"mastering failed: {err.strip()[-400:]}")
    after = media.audio_stats(dst)
    return {
        "before_lufs": float(m["input_i"]),
        "before_true_peak": float(m["input_tp"]),
        "after_lufs": after.integrated_lufs,
        "after_true_peak": after.true_peak_dbtp,
    }
