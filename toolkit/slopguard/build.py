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
# Number words stay with what follows ("seratus derajat", "ninety percent").
NUMBER_WORDS = {
    "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh", "sebelas",
    "seratus", "seribu", "sejuta", "puluh", "belas", "ratus", "ribu", "juta", "miliar", "triliun", "setengah",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand",
    "million", "billion", "half",
}


def _keeps_next(word: str, dangling: set) -> bool:
    bare = word.lower().strip(",.!?")
    if word.endswith((",", ".", "!", "?", ";", ":")):
        return False
    return bare in dangling or bare in NUMBER_WORDS or bool(re.fullmatch(r"[\d.,%]+", bare))


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
        score = abs(len(a) - len(b)) + (20 if _keeps_next(words[i - 1], DANGLING["id"] | DANGLING["en"]) else 0)
        if words[i - 1].endswith((",", ";", ":")):
            score -= 6
        if best_score is None or score < best_score:
            best, best_score = [a, b], score
    return best or [text]


READING_CPS = {"id": 17.0, "en": 20.0}  # Netflix adult reading speeds (Indonesian / English guides)
MIN_CUE = 5 / 6  # Netflix minimum event duration
MAX_CUE = 7.0


def _sentence_groups(words: List[Word], pause_break: float) -> List[List[Word]]:
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt is None:
            break
        if SENTENCE_END.search(w[0]) or nxt[1] - w[2] >= pause_break * 2:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def _balanced_split(group: List[Word], limit: int, max_dur: float, dangling: set, pause_break: float) -> List[List[Word]]:
    """Split one sentence into the fewest cues whose lengths are as even as possible,
    preferring breaks at commas and pauses and never ending a cue on a word that
    belongs to the next one (a preposition, an article, a number before its unit)."""
    n = len(group)
    texts = [w[0] for w in group]

    def length(i, j):
        return len(" ".join(texts[i:j]))

    total = length(0, n)
    if total <= limit and group[-1][2] - group[0][1] <= max_dur:
        return [group]

    def cost(i, j, target):
        L = length(i, j)
        if L > limit or (group[j - 1][2] - group[i][1]) > max_dur:
            return None
        c = ((L - target) / max(target, 1.0)) ** 2 * 100
        if j < n:
            if _keeps_next(texts[j - 1], dangling):
                c += 40
            if CLAUSE_END.search(texts[j - 1]):
                c -= 15
            if group[j][1] - group[j - 1][2] >= pause_break:
                c -= 15
        if j - i <= 2 and n > 4:
            c += 30  # orphan fragment
        return c

    import math

    best_cost, best_splits = None, None
    k0 = max(1, math.ceil(total / limit))
    for k in range(k0, min(n, k0 + 2) + 1):
        target = total / k
        INF = float("inf")
        dp = [[INF] * (n + 1) for _ in range(k + 1)]
        back = [[0] * (n + 1) for _ in range(k + 1)]
        dp[0][0] = 0.0
        for m in range(1, k + 1):
            for j in range(1, n + 1):
                for i in range(m - 1, j):
                    if dp[m - 1][i] == INF:
                        continue
                    c = cost(i, j, target)
                    if c is None:
                        continue
                    v = dp[m - 1][i] + c
                    if v < dp[m][j]:
                        dp[m][j], back[m][j] = v, i
        if dp[k][n] == INF:
            continue
        total_cost = dp[k][n] + 10 * (k - k0)
        if best_cost is None or total_cost < best_cost:
            cuts, j = [], n
            for m in range(k, 0, -1):
                i = back[m][j]
                cuts.append((i, j))
                j = i
            best_cost, best_splits = total_cost, list(reversed(cuts))
    if not best_splits:  # a single word longer than the limit, or an impossible duration
        out, cur = [], []
        for w in group:
            if cur and len(" ".join(x[0] for x in cur + [w])) > limit:
                out.append(cur)
                cur = []
            cur.append(w)
        return out + ([cur] if cur else [])
    return [group[i:j] for i, j in best_splits]


def captions_from_words(
    words: List[Word],
    lang: str = "id",
    max_chars: int = 42,
    max_lines: int = 2,
    max_cps: Optional[float] = None,
    min_dur: float = MIN_CUE,
    max_dur: float = 6.0,
    pause_break: float = 0.35,
    fps: float = 30.0,
    video_end: Optional[float] = None,
) -> List[Tuple[float, float, List[str]]]:
    """Word timings -> cues: sentence by sentence, balanced splits, <= max_lines lines,
    at least 5/6 s on screen when there is room, 2-frame gaps (Netflix timing rules)."""
    dangling = DANGLING.get(lang, set()) | DANGLING["en"]
    cps = max_cps or READING_CPS.get(lang, 17.0)
    gap = 2.0 / fps
    limit = max_chars * max_lines
    cues: List[List[Word]] = []
    for group in _sentence_groups(words, pause_break):
        cues.extend(_balanced_split(group, limit, max_dur, dangling, pause_break))

    out: List[Tuple[float, float, List[str]]] = []
    for idx, cue in enumerate(cues):
        text = " ".join(w[0] for w in cue)
        start, end = cue[0][1], cue[-1][2]
        next_start = cues[idx + 1][0][1] if idx + 1 < len(cues) else (video_end if video_end else end + 2.0)
        need = max(min_dur, len(text.replace(" ", "")) / cps)
        end = max(end, min(start + need, next_start - gap))
        end = min(end, next_start - gap, start + MAX_CUE) if idx + 1 < len(cues) else min(end, start + MAX_CUE)
        if video_end:
            end = min(end, video_end)
        out.append((start, max(end, start + 0.04), _split_lines(text, max_chars)))
    return out


def snap_to_cuts(cues, cuts: List[float], fps: float = 30.0):
    """Netflix shot-change timing: a cue ending within 12 frames before a cut ends 2 frames
    before it; a cue starting within 12 frames after a cut starts on it. Only moves times
    outward (never shortens a cue) and keeps the 2-frame gap to neighbours."""
    if not cuts:
        return cues
    f2, f12 = 2.0 / fps, 12.0 / fps
    out = [list(c) for c in cues]
    for i, c in enumerate(out):
        for cut in cuts:
            if 0 < cut - c[1] <= f12:
                limit = out[i + 1][0] - f2 if i + 1 < len(out) else cut
                c[1] = min(max(c[1], cut - f2), limit)
            if 0 < c[0] - cut <= f12:
                floor = out[i - 1][1] + f2 if i > 0 else 0.0
                c[0] = max(cut, floor)
    return [tuple(c) for c in out]


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
