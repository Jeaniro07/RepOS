"""Findings, tiers, waivers and report rendering shared by every check.

Tiers (borrowed in spirit from Nutlope/hallmark):
  FLOOR  - never ships. Fix it. Not waivable.
  REFLEX - a default that reads as generated. Fix it, or waive it on the
           record with a real reason (waivers.json).
  FINISH - craft note. Answer it; never blocks delivery.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Iterable, List, Optional

FLOOR = "FLOOR"
REFLEX = "REFLEX"
FINISH = "FINISH"
TIER_ORDER = {FLOOR: 0, REFLEX: 1, FINISH: 2}

# Exit codes used by the CLI.
EXIT_CLEAN = 0
EXIT_FLOOR = 1
EXIT_REFLEX = 2
EXIT_USAGE = 3


@dataclass
class Finding:
    gate: str
    tier: str
    message: str
    at: Optional[str] = None  # "12.40s", "line 7", "shot 3"
    fix: Optional[str] = None
    evidence: Optional[str] = None
    waived: bool = False
    waiver_reason: Optional[str] = None

    def label(self) -> str:
        if self.waived:
            return "WAIVED"
        return {FLOOR: "FAIL", REFLEX: "REFLEX", FINISH: "NOTE"}[self.tier]


@dataclass
class Report:
    subject: str
    kind: str
    findings: List[Finding] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    manual_checks: List[str] = field(default_factory=list)

    def add(self, *items: Finding) -> None:
        self.findings.extend(items)

    def extend(self, items: Iterable[Finding]) -> None:
        self.findings.extend(items)

    def sorted(self) -> List[Finding]:
        return sorted(self.findings, key=lambda f: (TIER_ORDER[f.tier], f.gate, f.at or ""))

    def open_floor(self) -> List[Finding]:
        return [f for f in self.findings if f.tier == FLOOR]

    def open_reflex(self) -> List[Finding]:
        return [f for f in self.findings if f.tier == REFLEX and not f.waived]

    def exit_code(self) -> int:
        if self.open_floor():
            return EXIT_FLOOR
        if self.open_reflex():
            return EXIT_REFLEX
        return EXIT_CLEAN

    def verdict(self) -> str:
        code = self.exit_code()
        if code == EXIT_FLOOR:
            return "BLOCKED: fix every FLOOR failure before anyone sees this."
        if code == EXIT_REFLEX:
            return "NOT YET: fix or waive (with a reason) every open REFLEX finding."
        return "CLEAR: no open FLOOR or REFLEX findings. Still review it with fresh eyes."

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "kind": self.kind,
            "verdict": self.verdict(),
            "exit_code": self.exit_code(),
            "counts": self.counts(),
            "metrics": self.metrics,
            "findings": [asdict(f) for f in self.sorted()],
            "manual_checks": self.manual_checks,
        }

    def counts(self) -> dict:
        c = {"floor": 0, "reflex_open": 0, "reflex_waived": 0, "finish": 0}
        for f in self.findings:
            if f.tier == FLOOR:
                c["floor"] += 1
            elif f.tier == REFLEX:
                c["reflex_waived" if f.waived else "reflex_open"] += 1
            else:
                c["finish"] += 1
        return c

    def to_markdown(self) -> str:
        c = self.counts()
        lines = [
            f"# slopguard {self.kind} report",
            "",
            f"- Subject: `{self.subject}`",
            f"- Verdict: **{self.verdict()}**",
            f"- Floor {c['floor']} FAIL · Reflex {c['reflex_open']} open"
            f" ({c['reflex_waived']} waived) · Finish {c['finish']} notes",
            "",
        ]
        if self.metrics:
            lines += ["## Measured", ""]
            for key, value in self.metrics.items():
                lines.append(f"- {key}: {_fmt(value)}")
            lines.append("")
        if self.findings:
            lines += ["## Findings", "", "| | Gate | Where | Problem | Fix |", "|---|---|---|---|---|"]
            for f in self.sorted():
                problem = f.message
                if f.waived:
                    problem += f" _(waived: {f.waiver_reason})_"
                if f.evidence:
                    problem += f" — `{f.evidence}`"
                lines.append(
                    f"| {f.label()} | `{f.gate}` | {f.at or '-'} | {_cell(problem)} | {_cell(f.fix or '')} |"
                )
            lines.append("")
        else:
            lines += ["No findings.", ""]
        if self.manual_checks:
            lines += ["## Not measurable here: check by eye/ear and say so", ""]
            lines += [f"- [ ] {item}" for item in self.manual_checks]
            lines.append("")
        lines.append(
            "_A measured pass is not a good video. Numbers catch what is broken; a fresh-context "
            "critic catches what is weak. Report what was measured and what nobody checked._"
        )
        return "\n".join(lines) + "\n"


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, (list, tuple)):
        return ", ".join(_fmt(v) for v in value) if value else "none"
    return str(value)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def load_waivers(path: Optional[str]) -> list:
    """Waivers are a JSON list (or {"waivers": [...]}) of
    {"gate": "picture.frozen", "reason": "...", "at": "41.0"(optional)}."""
    if not path:
        return []
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    items = data.get("waivers", []) if isinstance(data, dict) else data
    out = []
    for item in items:
        if not isinstance(item, dict) or not item.get("gate"):
            continue
        reason = str(item.get("reason", "")).strip()
        if len(reason) < 8:
            # A waiver without a real reason is not a waiver.
            continue
        out.append(item)
    return out


def apply_waivers(report: Report, waivers: list) -> None:
    for f in report.findings:
        if f.tier != REFLEX:
            continue  # FLOOR never waivable; FINISH never blocks.
        for w in waivers:
            if w["gate"] != f.gate:
                continue
            if w.get("at") is not None and not _at_matches(str(w["at"]), f.at):
                continue
            f.waived = True
            f.waiver_reason = str(w["reason"]).strip()
            break


def _at_matches(want: str, have: Optional[str]) -> bool:
    if have is None:
        return False
    try:
        a = float(want.rstrip("s"))
        b = float(have.split("-")[0].rstrip("s"))
        return abs(a - b) <= 0.75
    except ValueError:
        return want.strip() == have.strip()


def write_outputs(report: Report, out_dir: Optional[str], stem: str) -> List[str]:
    if not out_dir:
        return []
    os.makedirs(out_dir, exist_ok=True)
    md_path = os.path.join(out_dir, f"{stem}.md")
    json_path = os.path.join(out_dir, f"{stem}.json")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(report.to_markdown())
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report.to_dict(), fh, indent=2, ensure_ascii=False)
    return [md_path, json_path]
