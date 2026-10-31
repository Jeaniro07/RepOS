"""Shot ledger checks.

The ledger (ledger.csv) is the production evidence for every shot: what
is said, what idea it carries, what the viewer sees, and where that
picture comes from. It is how the agent proves a video is made from real
material and meaning rather than generic b-roll.

Columns (header row required, extra columns allowed):
  shot,start,end,narration,idea,visual,source_type,source,license,real_person,notes
source_type: footage | capture | code | illustration | generated | stock | archival | music | sfx
real_person: yes | no   (an identifiable real person appears or is depicted)
"""

from __future__ import annotations

import csv
import io
import os
from collections import Counter
from typing import List

from slopguard import provenance
from slopguard.report import FINISH, FLOOR, REFLEX, Finding, Report

SOURCE_TYPES = {"footage", "capture", "code", "illustration", "generated", "stock", "archival", "music", "sfx"}
NEEDS_SOURCE = {"footage", "capture", "stock", "archival", "music", "sfx"}
NEEDS_LICENSE = {"stock", "archival", "music", "sfx"}
REQUIRED = ["shot", "start", "end", "idea", "visual", "source_type"]


REAL_TYPES = {"footage", "capture", "archival", "stock"}


def check_ledger(text: str, subject: str = "ledger.csv", max_generated_share: float = 0.6, base_dir: str = None) -> Report:
    report = Report(subject=subject, kind="ledger")
    rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
    if not rows:
        report.add(Finding("ledger.empty", FLOOR, "Ledger has no shots.", fix="One row per shot before any generation or render."))
        return report
    header = [h.strip().lower() for h in rows[0].keys()]
    missing_cols = [c for c in REQUIRED if c not in header]
    if missing_cols:
        report.add(Finding("ledger.columns", FLOOR, f"Missing columns: {', '.join(missing_cols)}."))
        return report

    norm: List[dict] = [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in rows]
    total = 0.0
    ai_credentialed = [0]
    by_type: Counter = Counter()
    visuals: Counter = Counter()
    prev_end = None
    for r in norm:
        shot = r.get("shot") or "?"
        at = f"shot {shot}"
        try:
            start, end = float(r["start"]), float(r["end"])
        except ValueError:
            report.add(Finding("ledger.timing", FLOOR, "start/end are not numbers.", at=at))
            continue
        if end <= start:
            report.add(Finding("ledger.timing", FLOOR, f"end {end} <= start {start}.", at=at))
            continue
        dur = end - start
        total += dur
        if prev_end is not None:
            if start > prev_end + 0.05:
                report.add(Finding("ledger.gap", REFLEX, f"{start - prev_end:.2f}s gap before this shot.", at=at))
            elif start < prev_end - 0.05:
                report.add(Finding("ledger.overlap", FINISH, f"Overlaps the previous shot by {prev_end - start:.2f}s (fine for overlays).", at=at))
        prev_end = end

        st = r.get("source_type", "").lower()
        if st not in SOURCE_TYPES:
            report.add(Finding("ledger.source-type", FLOOR, f"Unknown source_type '{st}'.", at=at, fix=f"Use one of: {', '.join(sorted(SOURCE_TYPES))}."))
            continue
        by_type[st] += dur
        if not r.get("idea"):
            report.add(
                Finding(
                    "ledger.no-idea",
                    REFLEX,
                    "Shot has no idea: decoration, not communication.",
                    at=at,
                    fix="Write the one thing the viewer should understand from this shot, or cut it.",
                )
            )
        if st in NEEDS_SOURCE and not r.get("source"):
            report.add(Finding("ledger.no-source", FLOOR, f"{st} shot without a source (file, URL or capture page).", at=at))
        if st in NEEDS_LICENSE and not r.get("license"):
            report.add(
                Finding(
                    "ledger.no-license",
                    FLOOR,
                    f"{st} material without a license note.",
                    at=at,
                    fix="Record the license (CC BY 4.0 + credit, own recording, purchased, public domain...).",
                )
            )
        if st == "generated" and r.get("real_person", "").lower() in ("yes", "y", "ya", "true", "1"):
            if "consent" not in r.get("notes", "").lower() and "izin" not in r.get("notes", "").lower():
                report.add(
                    Finding(
                        "ledger.synthetic-real-person",
                        FLOOR,
                        "Generated picture of a real, identifiable person without recorded consent.",
                        at=at,
                        fix="Use real footage with permission, a non-identifiable illustration, or record 'consent: <who, when>' in notes.",
                    )
                )
        src = r.get("source", "")
        if base_dir and src:
            path = src if os.path.isabs(src) else os.path.join(base_dir, src)
            if os.path.isfile(path):
                info = provenance.inspect(path)
                if info.get("c2pa") and (info.get("ai_generated") or info.get("ai_in_history")):
                    gens = "; ".join(info.get("generators") or []) or "unknown generator"
                    if st in REAL_TYPES:
                        report.add(
                            Finding(
                                "ledger.provenance-mismatch",
                                FLOOR,
                                f"Listed as {st}, but the file's Content Credentials declare AI-generated content ({gens}).",
                                at=at,
                                fix="Mark it source_type=generated and disclose it, or replace it with real material.",
                            )
                        )
                    else:
                        ai_credentialed[0] += 1
        v = r.get("visual", "").lower()
        if v:
            visuals[v] += 1

    report.metrics["shots"] = len(norm)
    if base_dir:
        report.metrics["sources with AI Content Credentials"] = ai_credentialed[0]
    report.metrics["runtime in ledger (s)"] = round(total, 2)
    if total > 0:
        shares = {k: v / total for k, v in by_type.items()}
        report.metrics["runtime by source"] = ", ".join(f"{k} {v * 100:.0f}%" for k, v in sorted(shares.items(), key=lambda x: -x[1]))
        gen = shares.get("generated", 0.0)
        if gen > max_generated_share:
            report.add(
                Finding(
                    "ledger.generated-share",
                    REFLEX,
                    f"{gen * 100:.0f}% of the runtime is generated imagery.",
                    fix="Replace the weakest generated shots with real footage, captures of the real thing, or code-drawn diagrams that carry information.",
                )
            )
    for v, c in visuals.items():
        if c >= 3:
            report.add(
                Finding(
                    "ledger.repeat-visual",
                    REFLEX,
                    f"Same visual used {c} times: “{v[:60]}”",
                    fix="Change focal subject, viewpoint or action where the meaning changes.",
                )
            )
    return report
