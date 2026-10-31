---
name: video-assembly
description: Edit and render the video from approved script, ledger and assets with ffmpeg, HyperFrames, Remotion or Manim, keeping production hard rules (word-boundary cuts, 30 ms fades, captions last, -14 LUFS master). Use when cutting footage, building motion graphics, adding captions or music, or rendering a preview or final file.
---

# Assembling the video

Work in the project folder: sources in `assets/` (read-only), generated media in `gen/`, everything you
build in `edit/` (`edit/animations/<slot>/`, `edit/clips/`, `edit/master.srt`, `edit/preview.mp4`,
`edit/final.mp4`).

## Pick the engine per shot

| Shot | Engine | Why |
|---|---|---|
| Cutting real footage, talking head, interviews, screen recordings | ffmpeg (per-segment extract, then concat) | Exact, cheap, no re-encode chains |
| Kinetic type, UI motion, captions styles, data cards, product-page captures | HyperFrames (`npx --yes hyperframes ...`, Node 22+) | Deterministic HTML-to-video, lint/validate/snapshot built in |
| React component systems, existing Remotion brand kit | Remotion (`npx create-video@latest`, project-local) | When React is the simpler model; check the Remotion licence for companies |
| Equations, diagrams, graph morphs | Manim | Formal motion |
| Simple overlays (counter, bar reveal) | PIL frames + ffmpeg | Fast to iterate |

Scaffold each animation in its own `edit/animations/<slot>/` folder, render it, verify its duration and size
with `ffprobe`/`slopguard qa --no-sheets`, then place it in the edit. Fonts fail silently: in HTML engines,
await font loading and assert it before rendering; in PIL, pass an explicit font file.

The Rakazo computer has no Node by default. Before choosing HyperFrames or Remotion, run `node --version`;
if Node is missing, install it in your home folder (for example a Node 22 tarball from nodejs.org unpacked into
`~/.local/node` and added to PATH) or use ffmpeg/PIL instead. Say which you chose.

## Hard rules (correctness, not taste)

1. **Cut on word boundaries.** Use a word-level transcript; never cut inside a word. Pad each cut 30-200 ms.
   Prefer silences of 400 ms or more as cut points.
2. **Per-segment extract, then lossless concat** (`-c copy` on segments with identical codec settings), so
   overlays do not double-encode everything.
3. **30 ms audio fades at every segment boundary** (`afade=t=in:st=0:d=0.03,afade=t=out:st=<dur-0.03>:d=0.03`).
4. **Overlays shifted to their window** with `setpts=PTS-STARTPTS+<start>/TB`, so frame 0 of the animation
   appears at the window start.
5. **Captions are built on the output timeline** (`output_time = word.start - segment.start + segment.offset`)
   and **applied last**, after every overlay.
6. **Master once.** Mix to PCM, then two-pass `loudnorm=I=-14:TP=-1:LRA=11` on the final mix. Duck music
   12-15 dB under speech; ramp it out before the end card.
7. **Never stretch or speed up narration to fit pictures**; change the pictures.
8. **Deterministic renders**: no `Date.now()`/unseeded random in HTML/React; same input, same frames.
9. **Output spec** from `slopguard.json` (default vertical 1080x1920@30). H.264 yuv420p CRF 18-20,
   AAC 48 kHz, `-movflags +faststart`.

## Captions

- Chunk by meaning: keep names, numbers with units, and short phrases together; break at natural pauses.
- At most two lines, about 42 characters per line, at most 20 characters per second, each cue at least 0.7 s.
- Inside the title-safe area and above the platform buttons; never over the face or the product.
- Style is a choice in `SPEC.md`: short punchy chunks for fast social, natural sentences for explainers.
- Check: `slopguard check-captions edit/master.srt --video edit/preview.mp4`.

## Sound design

- Every effect is tied to something visible (a cut, a landing, a click). Fewer is better.
- Start an effect early by its attack time so the hit lands on the frame.
- Music is the user's taste call: offer two contrasting beds, never claim a mix sounds good; report the numbers.

## Preview

Render `edit/preview.mp4` (720p is fine), then run the `video-qa` skill before showing anything.
