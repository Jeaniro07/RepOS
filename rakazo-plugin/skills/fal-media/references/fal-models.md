# fal.ai endpoint starting points

Prices seen on fal pages and fal's own guides on 2026-10-31 (indicative; read the model page before every plan):
`fal-ai/nano-banana-pro` $0.15/image ($0.30 at 4K); `bytedance/seedance-2.0/image-to-video` about $0.30/s at 720p
(fast variant about $0.24/s), audio included; `fal-ai/elevenlabs/speech-to-text/scribe-v2` $0.008/min. fal's guide
also lists the newer `google/nano-banana-2.1`.

Snapshot taken 2026-10-31 from fal-ai-community/skills (`model-routing`, last updated 2026-05) and fal
model pages referenced there. Endpoints get renamed and replaced: **verify each id and its schema before
use** (fal model page, the fal MCP `search`/schema tools, or `genmedia models --endpoint_id <id> --json`).
Never invent an id. Prices change; read the model page or `genmedia pricing <id>` and put the number in
the generation plan.

## Stills

| Need | First choice | Alternatives |
|---|---|---|
| Fast cheap drafts (composition, mood) | `fal-ai/flux-2/klein/9b` | `fal-ai/flux/schnell`, `fal-ai/z-image/turbo` |
| Final stills, product/editorial realism | `openai/gpt-image-2` | `fal-ai/nano-banana-pro`, `fal-ai/nano-banana-2` |
| Edit from a reference (relight, replace background, keep identity) | `fal-ai/nano-banana-pro/edit` | `openai/gpt-image-2/edit`, `fal-ai/bytedance/seedream/v5/lite/edit` |
| Background removal / cutouts | `fal-ai/bria/background/remove` | |
| Upscale a still | `fal-ai/seedvr/upscale/image` | `fal-ai/topaz/upscale/image` |

Text inside images: avoid. If unavoidable (a sign in a scene), `openai/gpt-image-2` or `fal-ai/nano-banana-pro`,
then check every letter.

## Motion

| Need | First choice | Alternatives |
|---|---|---|
| Final image-to-video | `bytedance/seedance-2.0/image-to-video` | `fal-ai/kling-video/v3/pro/image-to-video`, `fal-ai/veo3.1` |
| Reference-to-video (keep a character/product) | `bytedance/seedance-2.0/reference-to-video` | `fal-ai/kling-video/o3/pro/reference-to-video` |
| Cheap motion previews | `xai/grok-imagine-video/image-to-video` | `bytedance/seedance-2.0/fast/image-to-video` |
| Multi-shot with element control | `fal-ai/kling-video/v3/pro/text-to-video` | |
| Lip-sync existing footage to new audio | `fal-ai/sync-lipsync/v2` | |
| Talking image + audio (only with consent of the person depicted) | `veed/fabric-1.0` | `fal-ai/creatify/aurora` |

Always image-to-video from an approved still rather than text-to-video for finals: the still is cheap to
iterate and fixes composition before paying for motion.

## Sound

| Need | Starting point |
|---|---|
| Word-level transcript (cuts, captions) | `fal-ai/elevenlabs/speech-to-text/scribe-v2` |
| Cheaper transcript | `fal-ai/wizper` |
| TTS narration | `fal-ai/elevenlabs/tts/eleven-v3`, `fal-ai/minimax/speech-2.6-hd`, `fal-ai/chatterbox/text-to-speech/multilingual` |
| Music bed (offer two contrasting options) | `fal-ai/elevenlabs/music` |
| Sound effects matched to a clip | `fal-ai/mmaudio-v2` |

## Utilities

`fal-ai/ffmpeg-api/extract-frame`, `fal-ai/ffmpeg-api/merge-videos`, `fal-ai/ffmpeg-api/merge-audio-video` exist,
but local ffmpeg (via `slopguard` setup) is free and deterministic: prefer it.
