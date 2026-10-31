# Gates

Three tiers (the structure is borrowed from Nutlope/hallmark's Floor / Reflex / Finish):

- **FLOOR**: never ships. Fix it. Waivers are ignored.
- **REFLEX**: a default a model falls into. Fix it, or waive it in `waivers.json` with a real reason
  (at least a sentence), e.g. `{"gate": "picture.frozen", "at": "41.0", "reason": "end card holds on the logo for 3 s by brief"}`.
- **FINISH**: craft notes. Answer them in `REVIEW.md`; they never block.

`slopguard` exit codes: 0 clean, 1 FLOOR failure, 2 open REFLEX, 3 setup/usage error.

## Script (`slopguard lint-script`)

| Gate | Tier | Meaning |
|---|---|---|
| script.unsourced-claim | FLOOR | A number, percentage, money amount, "studies show", "menurut penelitian"... without `[n]` |
| script.dangling-citation | FLOOR | `[n]` cited but missing from the Sources/Sumber list |
| script.empty | FLOOR | No narration found |
| script.generic-hook | REFLEX | "Halo guys", "Di video ini kita akan", "Have you ever", "Imagine"... as the first line |
| script.slop-density | REFLEX | Weighted stock-phrase hits >= 4 per 100 words |
| script.filler-opener / hype-word / hedge / signpost / cliche / contrast-frame | REFLEX (strong) or FINISH (weak) | Stock phrases; each finding carries a fix |
| script.engagement-bait / clickbait | REFLEX | "Jangan lupa like...", "simak sampai habis", "you won't believe" |
| script.monotone-rhythm | REFLEX | Sentence lengths barely vary (CV < 0.25) |
| script.rule-of-three | REFLEX | Too many "A, B dan C" lists |
| script.em-dash / question-stack / exclamation / emoji-hashtag | REFLEX | Written-text tells inside spoken narration |
| script.repetition | REFLEX | Same 4-word phrase 3+ times |
| script.crammed | REFLEX | Speech longer than the target (140 wpm ID, 155 wpm EN) |
| script.hook-too-long / sparse | FINISH | First sentence > 22 words; very little speech for the length |

## Ledger (`slopguard check-ledger`)

| Gate | Tier | Meaning |
|---|---|---|
| ledger.no-source | FLOOR | footage/capture/stock/archival/music/sfx row without a source |
| ledger.no-license | FLOOR | stock/archival/music/sfx row without a licence |
| ledger.synthetic-real-person | FLOOR | generated row with `real_person=yes` and no `consent:` in notes |
| ledger.source-type / timing / columns / empty | FLOOR | Malformed ledger |
| ledger.no-idea | REFLEX | A shot with no idea is decoration |
| ledger.generated-share | REFLEX | More than 60% of runtime is generated imagery |
| ledger.repeat-visual | REFLEX | Same visual 3+ times |
| ledger.gap | REFLEX | Hole in the shot timeline |

## Captions (`slopguard check-captions`, or `qa --captions`)

| Gate | Tier | Meaning |
|---|---|---|
| captions.overlap / beyond-end / timing / parse | FLOOR | Broken captions |
| captions.reading-speed | REFLEX | More than 20 characters per second |
| captions.flash | REFLEX | Cue on screen under 0.7 s |
| captions.line-length / lines | REFLEX | More than 32 characters per line on vertical video (42 on landscape), or more than 2 lines |
| captions.emoji | REFLEX | Emoji inside captions |
| captions.dense / long-hold / all-caps | FINISH | Comfort notes |

## Rendered video (`slopguard qa`)

| Gate | Tier | Meaning |
|---|---|---|
| video.decode | FLOOR | File does not decode / no video stream |
| video.size | FLOOR (wrong aspect) / REFLEX (right aspect, wrong resolution) | Against the target in `slopguard.json` |
| audio.missing / audio.silent | FLOOR | Over 15 s with no sound (unless `--silent-ok` by brief) |
| audio.clipping | FLOOR | True peak above -0.3 dBTP |
| picture.black | FLOOR (>= 2 s mid-video) / REFLEX | Black holes: a missing clip or failed overlay |
| audio.true-peak | REFLEX | True peak between -1 and -0.3 dBTP |
| audio.loudness | REFLEX | Integrated loudness outside -14 ± 2 LUFS |
| audio.dead-air | REFLEX | 1.5 s+ of silence mid-video |
| picture.frozen | REFLEX | Main picture (caption band and platform UI excluded) unchanged for 2.5 s+ |
| edit.slideshow | REFLEX | 40%+ of runtime frozen |
| edit.metronomic | REFLEX | 6+ cuts at near-identical intervals |
| picture.first-frame | REFLEX | Frame 0 black or flat (it is the thumbnail) |
| video.low-res / video.fps / video.duration | REFLEX | Under 720 px short side, under 24 fps, ±10% off target |
| encode.bitrate | FINISH | Thin bitrate; platform re-encode will band |

## Not measurable (always listed in the report as manual checks)

Truth of claims against the sources; whether the hook pays off; whether each object reads as what it is;
voice intelligibility over music; pops at cuts; whether anything sits under platform UI; AI disclosure;
that no real person is shown saying or doing what they did not.
