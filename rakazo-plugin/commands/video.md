---
description: Start a new anti-slop video project from a topic, link, script or footage
---

Start a new video with the antislop-video-director workflow for: $ARGUMENTS

1. Run `slopguard doctor`. If it fails, follow the video-toolkit-setup skill first.
2. Read everything the user attached or linked before asking anything.
3. Create the project with `slopguard init ~/videos/<short-slug> --title "<title>" --format <vertical|landscape|square> --duration <seconds> --lang <id|en>`
   (ask for format and length in the brief questions if they are not clear).
4. Ask the brief questions once (at most five), fill `BRIEF.md`, then propose three storylines with their hooks and recommend one.
5. Stop and wait for the user's choice unless they asked for autopilot. Paid fal.ai generation and publishing always need an explicit yes.
