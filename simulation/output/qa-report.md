# slopguard video report

- Subject: `edit/preview.mp4`
- Verdict: **CLEAR: no open FLOOR or REFLEX findings. Still review it with fresh eyes.**
- Floor 0 FAIL · Reflex 0 open (0 waived) · Finish 1 notes

## Measured

- size: 1080x1920
- duration (s): 19.80
- fps: 30.00
- video codec: h264
- audio: aac 48000 Hz
- target duration (s): 20
- bits per pixel: 0.03
- integrated loudness (LUFS): -14.00
- true peak (dBTP): -1.50
- loudness range (LU): 1.70
- dead-air gaps: 0
- frozen share of runtime: 0%
- first frame luma / range: 109 / 83
- cuts detected: 4
- mean shot length (s): 3.96
- cut times (s): 4.70, 7.17, 12.30, 16.97
- captions: cues: 7
- captions: mean reading speed (chars/s): 11.50
- ledger: shots: 5
- ledger: runtime in ledger (s): 19.75
- ledger: runtime by source: footage 50%, code 26%, generated 24%
- contact sheets: /tmp/antislop-sim-66x04nf1/home/videos/kopi-pahit/edit/qa/overview.jpg, /tmp/antislop-sim-66x04nf1/home/videos/kopi-pahit/edit/qa/cuts.jpg

## Findings

| | Gate | Where | Problem | Fix |
|---|---|---|---|---|
| NOTE | `encode.bitrate` | - | 1.9 Mb/s is thin for 1080x1920@30; expect banding/blocks after platform re-encode. | Encode H.264 CRF 18-20 (or 12+ Mb/s at 1080p). |

## Not measurable here: check by eye/ear and say so

- [ ] Watch it once at full speed on a phone-sized window; note the first moment you'd swipe away.
- [ ] Listen through headphones: voice intelligible over music, no pops at cuts, effects tied to visible events.
- [ ] Every on-screen object reads as what it is without a label; nothing important sits under platform UI.
- [ ] Realistic AI-generated people, places or events are disclosed on upload (platform 'altered or synthetic' label).
- [ ] Nothing shows a real person saying or doing something they did not say or do.
- [ ] Every cue matches the spoken words exactly (names, numbers, units kept together).
- [ ] Line breaks fall on natural phrase boundaries, not mid-phrase.
- [ ] Captions sit inside the title-safe area and never sit under platform UI or overlays.

_A measured pass is not a good video. Numbers catch what is broken; a fresh-context critic catches what is weak. Report what was measured and what nobody checked._
