---
description: Check a script, caption file, shot ledger or rendered video for AI slop and report what to fix
---

Check this for slop: $ARGUMENTS

Pick the check by file type and run it on the bot computer:

- `.md` / `.txt` script → `slopguard lint-script <file>`
- `.srt` / `.vtt` → `slopguard check-captions <file>` (add `--video <file>` if the render is known)
- `ledger.csv` → `slopguard check-ledger <file>`
- video file → `slopguard qa <file>` (add `--captions <file>` when there is one), then open `overview.jpg` and `cuts.jpg` from the report folder

If the user pasted text instead of a file, save it to a temporary `.md` file first. If they sent a link to a
video, ask for the file (do not download content they may not have rights to).

Reply with: the verdict line, the FLOOR failures (each with where and the fix), the top five REFLEX findings,
and what could not be measured. Offer to fix the script or the edit; do not change anything until they say yes.
