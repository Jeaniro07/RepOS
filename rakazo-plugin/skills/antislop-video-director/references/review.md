# Review

You wrote the timeline, so you know what happens. The viewer sees it once, at full speed, on a phone.
Review is how you see it as they will: as a harsh director, not a proud author.

## Order

1. `slopguard qa edit/final.mp4 --captions edit/master.srt` (the project's `slopguard.json` gives target,
   duration and loudness). Fix every FLOOR. Fix or waive every REFLEX.
2. Open `edit/qa/overview.jpg` and `edit/qa/cuts.jpg`. For each frame, describe in one sentence what a
   stranger sees, naming every object. An object you would have to explain is a P0.
3. Start the `slop-critic` helper with only: the brief, the spec, the script, the ledger, the QA report
   and the two contact sheets. Never give it your reasoning; fresh eyes are the point.
4. Fix: text first, then timing, then detail. Re-render, re-run `slopguard qa`, look again at the frames
   you changed only.
5. Stop after three passes. If anything is still open, tell the user exactly what and where.

## Notes format

One line per problem: `t=4.2s · where · problem → exact change · what stays`.

- **P0** breaks the read or the Floor: unreadable, wrong, unsourced, broken, a tell in the hook.
- **P1** weakens the video: a dead stretch, a soft payoff, a jump at a cut, a generic shot.
- **P2** polish.

Never score the video out of 10. A score finds nothing to fix.

## Questions to ask of the frames

| Question | Catches |
|---|---|
| Does frame 0 make someone stop scrolling? | Black/flat first frame, logo opening, greeting |
| Does each shot show the idea its narration says? | Decorative b-roll, recycled presenter shots |
| Would the pictures alone tell the story with the sound off? | Talking-over-wallpaper videos |
| Is anything generated pretending to be evidence? | Fake screenshots, fake documents, fake people |
| Can every line of text be read at phone size? | Text under 2.6% of the short side, under platform UI |
| What is the weakest shot, and why is it still there? | Filler |

## REVIEW.md (delivery note)

- The creative calls you made and the storylines you did not build.
- What was measured (numbers from the QA report) and what was only looked at; what nobody checked
  (you cannot hear: say so).
- The weakest shot and what you would change with more time.
- REFLEX gates waived and why.
- Generated shots and the AI-disclosure recommendation; credits and licences.
