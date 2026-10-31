"""Narration / script lint.

Reads a script (plain text or Markdown). Conventions understood:
  - Lines starting with '#' are headings, not narration.
  - [VISUAL: ...], [B-ROLL ...], {...} and any other [bracketed note] are
    stage directions and are not linted as speech.
  - Citations are [1], [12] or [src: ...] / [sumber: ...] inside the sentence.
  - A section that starts with a line "Sources:" / "Sumber:" / "Referensi:"
    (or a heading with those words) ends the narration; what follows is the
    source list.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from typing import List, Optional, Tuple

from slopguard import lexicon
from slopguard.report import FINISH, FLOOR, REFLEX, Finding, Report

CITATION_RE = re.compile(r"\[(\d+|src:[^\]]+|sumber:[^\]]+|source:[^\]]+)\]", re.I)
DIRECTION_RE = re.compile(r"\[[^\]]*\]|\{[^}]*\}")
SOURCES_HEAD_RE = re.compile(r"^\s*(#+\s*)?(sources?|sumber|referensi|references)\s*:?\s*$", re.I)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+|\n+")
WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9']+(?:-[A-Za-zÀ-ÿ0-9']+)*")
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U0001F900-\U0001F9FF]"
)
TRIPLET_EN = re.compile(r"\b[\w'-]+(?: [\w'-]+){0,2}, [\w'-]+(?: [\w'-]+){0,2},? and [\w'-]+", re.I)
TRIPLET_ID = re.compile(r"\b[\w'-]+(?: [\w'-]+){0,2}, [\w'-]+(?: [\w'-]+){0,2},? dan [\w'-]+", re.I)


def split_narration(text: str) -> Tuple[List[Tuple[int, str]], str, bool]:
    """Return ([(line_no, narration_line)], sources_text, has_sources_section)."""
    narration: List[Tuple[int, str]] = []
    sources_lines: List[str] = []
    in_sources = False
    for i, raw in enumerate(text.splitlines(), start=1):
        if SOURCES_HEAD_RE.match(raw):
            in_sources = True
            continue
        if in_sources:
            sources_lines.append(raw)
            continue
        line = raw.strip()
        if not line or line.startswith("#") or line.lower().startswith("> note"):
            continue
        if line.startswith("|") or line.startswith("---"):
            continue
        narration.append((i, line))
    return narration, "\n".join(sources_lines), in_sources


def detect_language(text: str) -> str:
    words = [w.lower() for w in WORD_RE.findall(text)]
    en = sum(1 for w in words if w in lexicon.FUNCTION_WORDS_EN)
    idn = sum(1 for w in words if w in lexicon.FUNCTION_WORDS_ID)
    return "id" if idn > en else "en"


def _sentences(narration: List[Tuple[int, str]]) -> List[Tuple[int, str, str]]:
    """[(line_no, sentence_with_citations, spoken_sentence)]"""
    out = []
    for line_no, line in narration:
        for piece in SENTENCE_SPLIT_RE.split(line):
            piece = piece.strip()
            if not piece:
                continue
            spoken = DIRECTION_RE.sub(" ", piece)
            spoken = re.sub(r"\s+", " ", spoken).strip(" -–—*_")
            if not WORD_RE.search(spoken):
                continue
            out.append((line_no, piece, spoken))
    return out


def lint_script(
    text: str,
    lang: str = "auto",
    target_seconds: Optional[float] = None,
    subject: str = "script",
    extra_lexicon: Optional[list] = None,
) -> Report:
    narration, sources_text, has_sources = split_narration(text)
    sentences = _sentences(narration)
    spoken_all = " ".join(s for _, _, s in sentences)
    if lang == "auto":
        lang = detect_language(spoken_all or text)
    words = WORD_RE.findall(spoken_all)
    n_words = len(words)
    report = Report(subject=subject, kind="script")
    report.metrics["language"] = lang
    report.metrics["spoken words"] = n_words
    report.metrics["sentences"] = len(sentences)

    if n_words == 0:
        report.add(Finding("script.empty", FLOOR, "No narration found.", fix="Write the narration, or check the file."))
        return report

    wpm = lexicon.SPEAKING_WPM.get(lang, 150)
    est_seconds = n_words / wpm * 60.0
    report.metrics["estimated read time (s)"] = round(est_seconds, 1)

    # 1. Phrase lexicon.
    entries = list(lexicon.ID if lang == "id" else lexicon.EN)
    if lang == "id":
        # English hype words and bait leak into Indonesian scripts too.
        entries += [e for e in lexicon.EN if e[2] in (lexicon.HYPE, lexicon.BAIT) and e[1] >= 3]
    for item in extra_lexicon or []:
        try:
            entries.append((str(item[0]), int(item[1]), str(item[2]), str(item[3]) if len(item) > 3 else ""))
        except (IndexError, TypeError, ValueError):
            continue
    weighted = 0
    category_hits: Counter = Counter()
    for line_no, _, spoken in sentences:
        seen_spans: list = []
        for pattern, weight, category, hint in entries:
            for m in re.finditer(pattern, spoken, re.I):
                if any(m.start() < e and s < m.end() for s, e in seen_spans):
                    continue  # same words already matched by another list
                seen_spans.append((m.start(), m.end()))
                weighted += weight
                category_hits[category] += 1
                tier = REFLEX if weight >= 3 or category in (lexicon.BAIT, lexicon.CLICKBAIT) else FINISH
                report.add(
                    Finding(
                        f"script.{category}",
                        tier,
                        f"Stock phrase: “{m.group(0)}”",
                        at=f"line {line_no}",
                        fix=hint,
                    )
                )
    density = weighted / max(n_words, 1) * 100
    report.metrics["slop score (weighted hits / 100 words)"] = round(density, 2)
    if density >= 4:
        report.add(
            Finding(
                "script.slop-density",
                REFLEX,
                f"Stock-phrase density {density:.1f} per 100 words; reads as generated.",
                fix="Rewrite from the brief: one concrete claim per sentence, said the way you'd say it out loud.",
            )
        )

    # 2. Unsourced factual claims (FLOOR: never invent facts).
    cues = lexicon.CLAIM_CUES_ID if lang == "id" else lexicon.CLAIM_CUES_EN
    cues = cues + (lexicon.CLAIM_CUES_EN if lang == "id" else [])
    unsourced = 0
    for line_no, with_cites, spoken in sentences:
        if any(re.search(c, spoken, re.I) for c in cues) and not CITATION_RE.search(with_cites):
            unsourced += 1
            report.add(
                Finding(
                    "script.unsourced-claim",
                    FLOOR,
                    f"Factual claim without a citation: “{_clip(spoken)}”",
                    at=f"line {line_no}",
                    fix="Add [n] pointing to a source in the Sources/Sumber section, soften it to opinion, or cut it.",
                )
            )
    cited_ids = set(re.findall(r"\[(\d+)\]", "\n".join(w for _, w, _ in sentences)))
    if cited_ids:
        listed = set(re.findall(r"^\s*\[?(\d+)[\].)]", sources_text, re.M))
        missing = sorted(cited_ids - listed, key=int)
        if missing:
            report.add(
                Finding(
                    "script.dangling-citation",
                    FLOOR,
                    f"Citation(s) {', '.join('[' + m + ']' for m in missing)} have no entry in the Sources section.",
                    fix="List every cited source as '[n] title, publisher, date, URL'.",
                )
            )
    report.metrics["unsourced claims"] = unsourced

    # 3. Hook.
    first = sentences[0][2]
    hook_patterns = lexicon.GENERIC_HOOK_ID if lang == "id" else lexicon.GENERIC_HOOK_EN
    if any(re.search(p, first, re.I) for p in hook_patterns):
        report.add(
            Finding(
                "script.generic-hook",
                REFLEX,
                f"Generic opening line: “{_clip(first)}”",
                at=f"line {sentences[0][0]}",
                fix="Open on the most specific, surprising true thing you have, or show the result first.",
            )
        )
    first_len = len(WORD_RE.findall(first))
    if first_len > 22:
        report.add(
            Finding(
                "script.hook-too-long",
                FINISH,
                f"First sentence is {first_len} words; the hook has about 2-3 seconds.",
                at=f"line {sentences[0][0]}",
                fix="Cut the first line to 12 words or fewer.",
            )
        )

    # 4. Rhythm: sentence-length variation (burstiness).
    lengths = [len(WORD_RE.findall(s)) for _, _, s in sentences]
    if len(lengths) >= 6:
        mean = statistics.mean(lengths)
        cv = statistics.pstdev(lengths) / mean if mean else 0.0
        report.metrics["sentence length mean / CV"] = f"{mean:.1f} words / {cv:.2f}"
        if cv < 0.25:
            report.add(
                Finding(
                    "script.monotone-rhythm",
                    REFLEX,
                    f"Sentence lengths barely vary (CV {cv:.2f}); spoken it sounds like a template.",
                    fix="Mix short punches (3-6 words) with longer explanations; read it aloud.",
                )
            )

    # 5. Structure tells.
    triplet_re = TRIPLET_ID if lang == "id" else TRIPLET_EN
    triplets = sum(len(triplet_re.findall(s)) for _, _, s in sentences)
    if triplets >= 3 and triplets / max(len(sentences), 1) > 0.15:
        report.add(
            Finding(
                "script.rule-of-three",
                REFLEX,
                f"{triplets} 'A, B and C' lists in {len(sentences)} sentences.",
                fix="Keep the one list that matters; give the others one specific item.",
            )
        )
    dashes = spoken_all.count("—") + spoken_all.count(" -- ")
    if dashes and dashes / max(n_words, 1) * 100 > 1.0:
        report.add(
            Finding(
                "script.em-dash",
                REFLEX,
                f"{dashes} em dashes in {n_words} words.",
                fix="Narration is heard, not read: use full stops.",
            )
        )
    questions = sum(1 for _, _, s in sentences if s.rstrip().endswith("?"))
    if len(sentences) >= 5 and questions / len(sentences) > 0.3:
        report.add(
            Finding(
                "script.question-stack",
                REFLEX,
                f"{questions} of {len(sentences)} sentences are questions.",
                fix="Answer more than you ask.",
            )
        )
    exclaims = spoken_all.count("!")
    if exclaims and exclaims / max(len(sentences), 1) > 0.2:
        report.add(
            Finding(
                "script.exclamation",
                REFLEX,
                f"{exclaims} exclamation marks; energy should come from content and delivery.",
                fix="Keep at most one.",
            )
        )
    raw_narration = " ".join(DIRECTION_RE.sub(" ", line) for _, line in narration)
    emojis = len(EMOJI_RE.findall(raw_narration))
    hashtags = len(re.findall(r"(?<!\w)#\w+", raw_narration))
    if emojis >= 3 or hashtags >= 3:
        report.add(
            Finding(
                "script.emoji-hashtag",
                REFLEX,
                f"{emojis} emoji and {hashtags} hashtags inside the narration.",
                fix="Narration is spoken; move tags to the post caption.",
            )
        )

    # 6. Repetition: same 4-word phrase used 3+ times.
    lowered = [w.lower() for w in words]
    grams = Counter(tuple(lowered[i : i + 4]) for i in range(len(lowered) - 3))
    repeats = [(" ".join(g), c) for g, c in grams.items() if c >= 3]
    if repeats:
        top = ", ".join(f"“{g}” ×{c}" for g, c in sorted(repeats, key=lambda x: -x[1])[:3])
        report.add(
            Finding(
                "script.repetition",
                REFLEX,
                f"Repeated phrasing: {top}.",
                fix="Say each idea once; a callback is fine when it is deliberate.",
            )
        )

    # 7. Length against target.
    if target_seconds:
        report.metrics["target duration (s)"] = target_seconds
        if est_seconds > target_seconds * 1.10:
            report.add(
                Finding(
                    "script.crammed",
                    REFLEX,
                    f"About {est_seconds:.0f}s of speech for a {target_seconds:.0f}s video at {wpm} wpm.",
                    fix=f"Cut to about {int(target_seconds * wpm / 60)} words. Cut words, never speed up the voice.",
                )
            )
        elif est_seconds < target_seconds * 0.45:
            report.add(
                Finding(
                    "script.sparse",
                    FINISH,
                    f"Only about {est_seconds:.0f}s of speech for {target_seconds:.0f}s; the picture must carry the rest.",
                    fix="Plan what the viewer watches in the silences, or shorten the video.",
                )
            )

    report.manual_checks += [
        "Every claim is true and the cited source actually says it (open each link).",
        "Read the script aloud once at speaking pace; mark where you stumble.",
        "The hook promise is paid off in the body, not just teased.",
        "Names, numbers and dates match the sources and the on-screen text.",
    ]
    if category_hits:
        report.metrics["hits by category"] = ", ".join(f"{k} {v}" for k, v in category_hits.most_common())
    return report


def _clip(text: str, n: int = 90) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"
