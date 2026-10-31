"""Caption (SRT / WebVTT) checks: readability and timing.

Defaults follow common broadcast/streaming practice for adult viewers:
at most 2 lines, about 42 characters per line, reading speed at most
about 17-20 characters per second, cues on screen at least ~0.7 s.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from slopguard.report import FINISH, FLOOR, REFLEX, Finding, Report

TIME_RE = re.compile(
    r"(?P<a>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}|\d{1,2}:\d{2}[,.]\d{1,3})\s*-->\s*"
    r"(?P<b>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}|\d{1,2}:\d{2}[,.]\d{1,3})"
)
TAG_RE = re.compile(r"<[^>]+>|\{\\[^}]*\}")
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F900-\U0001F9FF]")


@dataclass
class Cue:
    index: int
    start: float
    end: float
    lines: List[str]
    line_no: int

    @property
    def text(self) -> str:
        return " ".join(self.lines)

    @property
    def duration(self) -> float:
        return self.end - self.start


def _ts(value: str) -> float:
    value = value.replace(",", ".")
    parts = value.split(":")
    if len(parts) == 2:
        parts = ["0"] + parts
    h, m, s = parts
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_captions(text: str) -> List[Cue]:
    cues: List[Cue] = []
    lines = text.replace("﻿", "").splitlines()
    i = 0
    n = 0
    while i < len(lines):
        m = TIME_RE.search(lines[i])
        if not m:
            i += 1
            continue
        start, end = _ts(m.group("a")), _ts(m.group("b"))
        line_no = i + 1
        i += 1
        body = []
        while i < len(lines) and lines[i].strip() != "":
            if TIME_RE.search(lines[i]):
                break
            body.append(TAG_RE.sub("", lines[i]).strip())
            i += 1
        n += 1
        cues.append(Cue(n, start, end, [b for b in body if b], line_no))
    return cues


# Netflix Timed Text Style Guide: adult reading speed 17 cps (Indonesian guide) / 20 cps
# (English guide), events between 5/6 s and 7 s, at least 2 frames between events.
READING_CPS = {"id": 17.0, "en": 20.0}


def check_captions(
    text: str,
    subject: str = "captions",
    video_duration: Optional[float] = None,
    max_cps: Optional[float] = None,
    comfortable_cps: float = 15.0,
    max_chars: int = 42,
    max_lines: int = 2,
    min_duration: float = 0.7,
    max_duration: float = 7.0,
    lang: Optional[str] = None,
    fps: float = 30.0,
) -> Report:
    report = Report(subject=subject, kind="captions")
    if max_cps is None:
        max_cps = READING_CPS.get(lang or "", 20.0)
    report.metrics["reading-speed limit (chars/s)"] = max_cps
    min_gap = 2.0 / fps
    cues = parse_captions(text)
    report.metrics["cues"] = len(cues)
    if not cues:
        report.add(Finding("captions.parse", FLOOR, "No cues could be parsed.", fix="Export SRT or WebVTT with timestamps."))
        return report

    fast, flashes, long_lines, many_lines, emoji = 0, 0, 0, 0, 0
    caps_cues = 0
    cps_values = []
    prev: Optional[Cue] = None
    for cue in cues:
        at = f"{cue.start:.2f}s"
        if cue.end <= cue.start:
            report.add(Finding("captions.timing", FLOOR, f"Cue {cue.index} ends before it starts.", at=at))
            continue
        if prev and cue.start < prev.end - 0.01:
            report.add(
                Finding(
                    "captions.overlap",
                    FLOOR,
                    f"Cue {cue.index} starts {prev.end - cue.start:.2f}s before cue {prev.index} ends.",
                    at=at,
                    fix="Captions must not overlap; end the earlier cue first.",
                )
            )
        if video_duration and cue.end > video_duration + 0.05:
            report.add(
                Finding(
                    "captions.beyond-end",
                    FLOOR,
                    f"Cue {cue.index} ends at {cue.end:.2f}s, after the video ends ({video_duration:.2f}s).",
                    at=at,
                    fix="Captions use output-timeline offsets; rebuild them from the final edit.",
                )
            )
        chars = len(cue.text.replace(" ", ""))
        cps = chars / cue.duration if cue.duration > 0 else 99
        cps_values.append(cps)
        if cps > max_cps:
            fast += 1
            report.add(
                Finding(
                    "captions.reading-speed",
                    REFLEX,
                    f"Cue {cue.index} needs {cps:.0f} chars/s (max {max_cps:.0f}): “{_clip(cue.text)}”",
                    at=at,
                    fix="Hold it longer, or cut words. Never shrink the type.",
                )
            )
        if cue.duration < min_duration:
            flashes += 1
            report.add(
                Finding(
                    "captions.flash",
                    REFLEX,
                    f"Cue {cue.index} is on screen {cue.duration:.2f}s.",
                    at=at,
                    fix=f"Merge with a neighbour so every cue stays at least {min_duration:.1f}s.",
                )
            )
        elif cue.duration < 5 / 6 - 1e-6:
            report.add(
                Finding(
                    "captions.short",
                    FINISH,
                    f"Cue {cue.index} is on screen {cue.duration:.2f}s (streaming minimum is 5/6 s).",
                    at=at,
                    fix="Fine for punchy 1-3 word captions by design; otherwise hold it longer.",
                )
            )
        if prev and 0 <= cue.start - prev.end < min_gap - 1e-6:
            report.add(
                Finding(
                    "captions.gap",
                    FINISH,
                    f"Only {(cue.start - prev.end) * 1000:.0f} ms between cue {prev.index} and {cue.index} (want >= 2 frames).",
                    at=at,
                    fix="End the earlier cue 2 frames before the next one starts, so the change reads as a new cue.",
                )
            )
        if cue.duration > max_duration:
            report.add(Finding("captions.long-hold", FINISH, f"Cue {cue.index} stays {cue.duration:.1f}s.", at=at))
        for line in cue.lines:
            if len(line) > max_chars:
                long_lines += 1
                report.add(
                    Finding(
                        "captions.line-length",
                        REFLEX,
                        f"Line of {len(line)} chars (max {max_chars}): “{_clip(line)}”",
                        at=at,
                        fix="Break at a natural phrase boundary.",
                    )
                )
        if len(cue.lines) > max_lines:
            many_lines += 1
            report.add(Finding("captions.lines", REFLEX, f"Cue {cue.index} has {len(cue.lines)} lines.", at=at))
        if EMOJI_RE.search(cue.text):
            emoji += 1
        letters = [c for c in cue.text if c.isalpha()]
        if len(letters) > 8 and all(c.isupper() for c in letters):
            caps_cues += 1
        prev = cue

    if emoji:
        report.add(
            Finding(
                "captions.emoji",
                REFLEX,
                f"{emoji} cues contain emoji.",
                fix="Captions carry speech; emoji in captions is a template tell.",
            )
        )
    if cps_values:
        avg = sum(cps_values) / len(cps_values)
        report.metrics["mean reading speed (chars/s)"] = round(avg, 1)
        if avg > comfortable_cps:
            report.add(
                Finding(
                    "captions.dense",
                    FINISH,
                    f"Average {avg:.1f} chars/s is above a comfortable {comfortable_cps:.0f}.",
                    fix="Trim filler words from captions (keep meaning).",
                )
            )
    if caps_cues and caps_cues / len(cues) > 0.6:
        report.metrics["all-caps cues"] = caps_cues
        report.add(
            Finding(
                "captions.all-caps",
                FINISH,
                "Most cues are ALL CAPS. Fine for 1-3 word punch captions; tiring for full sentences.",
            )
        )
    report.manual_checks += [
        "Every cue matches the spoken words exactly (names, numbers, units kept together).",
        "Line breaks fall on natural phrase boundaries, not mid-phrase.",
        "Captions sit inside the title-safe area and never sit under platform UI or overlays.",
    ]
    return report


def _clip(text: str, n: int = 60) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def near_cut_findings(cues: List[Cue], cuts: List[float], fps: float = 30.0) -> List[Finding]:
    """Cue in/out times that land close to, but not on, a shot change flash on screen.
    Netflix guidance: snap to the shot change (out-time 2 frames before it) or keep
    at least 12 frames away."""
    out: List[Finding] = []
    if not cuts:
        return out
    snap, keep_away = 2.0 / fps, 12.0 / fps
    for cue in cues:
        for label, t in (("starts", cue.start), ("ends", cue.end)):
            nearest = min(cuts, key=lambda c: abs(c - t))
            dist = abs(nearest - t)
            if snap < dist < keep_away:
                out.append(
                    Finding(
                        "captions.near-cut",
                        FINISH,
                        f"Cue {cue.index} {label} {dist * 1000:.0f} ms from the shot change at {nearest:.2f}s.",
                        at=f"{t:.2f}s",
                        fix="Snap the cue to the cut (out-time 2 frames before it) or keep it 12+ frames away.",
                    )
                )
    return out
