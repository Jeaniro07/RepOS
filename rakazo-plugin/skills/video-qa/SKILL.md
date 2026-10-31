---
name: video-qa
description: Check a rendered video before anyone sees it, with measured gates (loudness, clipping, dead air, frozen or black picture, metronomic cuts, captions, sources, licences), contact sheets and an independent slop-critic review, then write REVIEW.md. Use after every preview or final render, or when the user asks whether a video is slop, ready, or good enough.
---

# Video QA

## 1. Measure

```bash
slopguard qa edit/preview.mp4 --captions edit/master.srt
```

Inside a project folder, `slopguard.json` supplies the target size, duration and loudness, `ledger.csv` is
checked too, `waivers.json` is applied, and the report plus contact sheets land in `edit/qa/`:
`qa-report.md`, `qa-report.json`, `overview.jpg` (20 frames), `cuts.jpg` (before/after every cut) and, for
vertical video, `safezones.jpg` (frames with the platform-UI bands shaded red and the safe box in green).
The measured gates include temporal flicker (a generated-video tell), caption reading speed for the project's
language, 2-frame caption gaps and captions that land just beside a shot change.

Exit code 1 means a FLOOR failure: fix it, there is no waiver. Exit code 2 means open REFLEX findings: fix
each one, or waive it with a real reason in `waivers.json` (example: a deliberate 3 s hold on the end card).
Gate meanings: `antislop-video-director` → `references/floor.md`.

## 2. Look

Open `overview.jpg` and `cuts.jpg`. For each frame write one sentence a stranger would say about it. Check:
frame 0 works as a thumbnail; every shot shows the idea of its narration; nothing important sits under
platform UI (check `safezones.jpg`); text is readable at phone size; no caption wraps to 3+ lines; no generated artifact (hands, text, faces, physics); no jump or
flash at cuts. Use `slopguard sheet <video> --out edit/qa/zoom --count 12` on a section that needs a closer look.

## 3. Independent critic

Start the `slop-critic` helper. Give it only: `BRIEF.md`, `SPEC.md`, `script.md`, `ledger.csv`,
`edit/qa/qa-report.md`, `edit/qa/overview.jpg`, `edit/qa/cuts.jpg` (and `edit/qa/safezones.jpg` for vertical
video). Do not give it your reasoning or your
opinion of the video. Take its P0 and P1 notes seriously; you are biased toward your own work.

## 4. Fix loop

Fix text first, then timing, then detail. Re-render, re-run `slopguard qa`, and look only at what changed.
At most three passes. If something is still open after three, stop and tell the user exactly what, where
(timecode) and what you would try next.

## 5. Report

Write `REVIEW.md` (format in `antislop-video-director` → `references/review.md`) and give the user its
short form: verdict line from the QA report, the numbers (LUFS, true peak, cuts, frozen share, caption
speed), waived gates with reasons, the weakest shot, generated shots and the AI-disclosure recommendation,
and an honest line that you measured but could not watch or listen.
