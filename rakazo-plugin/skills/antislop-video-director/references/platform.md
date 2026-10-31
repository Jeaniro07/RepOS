# Platform notes

Policies change. Before telling the user what a platform requires, open the platform's current policy
page and quote it. The notes below are a starting point, not a source.

## Delivery formats

| Target | Size | fps | Notes |
|---|---|---|---|
| Shorts / Reels / TikTok | 1080x1920 (9:16) | 30 | Keep text and faces out of the bottom ~25%, the right ~12% (buttons) and the top ~8% |
| YouTube landscape | 1920x1080 (16:9) | 24/25/30 | Thumbnail-worthy frame 0 still matters for previews |
| Feed square / portrait | 1080x1080, 1080x1350 | 30 | Captions inside the centre 80% |

Encode: H.264 High, yuv420p, CRF 18-20 (or 12+ Mb/s at 1080p), AAC 48 kHz 192 kb/s+, `+faststart`.

## Loudness

Master the final mix once: two-pass `loudnorm=I=-14:TP=-1:LRA=11` (or your platform's target), then
measure with `slopguard qa`. Measure per section too (speech, music-only, end card): an end card 15 dB under
the dialogue is a bug.

## AI disclosure and authenticity (check the current wording)

- YouTube asks creators to disclose realistic altered or synthetic content in the upload flow, and its
  monetisation policy covers mass-produced, repetitive ("inauthentic") content. Templated slop is exactly
  what that policy targets.
- TikTok asks for an AI-generated label on realistic AI content and may label it automatically.
- Meta (Instagram/Facebook) shows "AI info" labels and asks for disclosure of photorealistic AI video/audio.

Your delivery note always says which shots are generated (from `ledger.csv`) and whether the platform
disclosure toggle should be on. The user makes that call; you make sure they can.

## Rights

- Music: only licensed, owned or properly licensed library tracks; record the licence in the ledger.
- Fonts: licensed for video; open fonts (OFL) are fine.
- People: no identifiable person without consent; no voice cloning without the owner's consent.
- Brands: real logos only where the brand is the actual subject, never implying endorsement.
