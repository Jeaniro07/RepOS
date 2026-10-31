# Platform notes

Policies change. Before telling the user what a platform requires, open the platform's current policy
page and quote it. The notes below are a starting point, not a source.

## Delivery formats

| Target | Size | fps | Notes |
|---|---|---|---|
| Shorts / Reels / TikTok | 1080x1920 (9:16) | 30 | Platform UI covers roughly the top 120-200 px, bottom 250-370 px, right 120-164 px, left 50-60 px. Keep text, faces and products inside the central ~900x1400 box. `slopguard qa` draws this on `safezones.jpg`. Figures are from vendor guides, not official specs: check in each app |
| YouTube landscape | 1920x1080 (16:9) | 24/25/30 | Thumbnail-worthy frame 0 still matters for previews |
| Feed square / portrait | 1080x1080, 1080x1350 | 30 | Captions inside the centre 80% |

Encode: H.264 High, yuv420p, CRF 18-20 (or 12+ Mb/s at 1080p), AAC 48 kHz 192 kb/s+, `+faststart`.

## Loudness

Master the final mix once: two-pass `loudnorm=I=-14:TP=-1:LRA=11` (or your platform's target), then
measure with `slopguard qa`. Measure per section too (speech, music-only, end card): an end card 15 dB under
the dialogue is a bug.

## AI disclosure and authenticity (check the current wording)

As reported in the press (verify on YouTube Help before quoting it to the user):

- **Altered or synthetic content (YouTube, since March 2024):** creators tick a disclosure box for realistic
  content made with altered or synthetic media. Clearly unrealistic, animated or effects content, and AI used
  only for production help (scripts, ideas), is exempt. Sensitive topics (health, news, elections, finance) get a
  more visible label.
- **Automatic labels (YouTube, May 2026):** YouTube now applies an AI label itself when it detects significant
  photorealistic AI use that was not disclosed, uses C2PA metadata as one signal, and shows the label more
  prominently (an overlay on Shorts). Labels from C2PA "fully generative" metadata cannot be disputed.
- **"Captured with a camera" (YouTube):** a provenance label for unedited footage from C2PA 2.1+ cameras/apps.
  Any edit and re-encode (everything this workflow does) removes it; that is expected.
- **Inauthentic content (YouTube Partner Program, from 15 July 2025):** mass-produced and repetitive uploads are
  not monetised. YouTube called it a clarification of existing rules; coverage read it as aimed at AI slop.
- **False positives happen.** In 2026 YouTube's detection wrongly penalised a human-made Kurzgesagt video. Keep the
  production evidence (ledger, sources, raw files list, `project.md`, `REVIEW.md`) so the user can appeal.
- TikTok asks for an AI-generated label on realistic AI content and may label it automatically; Meta shows "AI info".

Your delivery note always says which shots are generated (from `ledger.csv`) and whether the platform
disclosure toggle should be on. The user makes that call; you make sure they can.

## Rights

- Music: only licensed, owned or properly licensed library tracks; record the licence in the ledger.
- Fonts: licensed for video; open fonts (OFL) are fine.
- People: no identifiable person without consent; no voice cloning without the owner's consent.
- Brands: real logos only where the brand is the actual subject, never implying endorsement.
