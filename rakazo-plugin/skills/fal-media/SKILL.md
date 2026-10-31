---
name: fal-media
description: Generate or process images, video clips, voice, music, sound and transcripts with fal.ai for a video project, with an approved plan and a spending guard. Use whenever a shot, voiceover, transcript, upscale, background removal or lip-sync needs fal.ai, or when the user mentions fal, FAL_KEY, Nano Banana, Kling, Seedance, Veo, ElevenLabs on fal or Scribe.
---

# fal.ai for anti-slop video

fal.ai is a paid API. Treat every call as spending the user's money and every output as a draft that must
earn its place in the video.

## The key

Never ask the user to paste the key in chat and never print it. Two supported routes:

1. **Command variable (for `slopguard fal`)**: call `request_secret` with
   `{"label": "fal.ai API key", "purpose": "api_key", "credential": {"name": "fal-key", "auth": {"type": "command"}}}`.
   Rakazo then exports it to your shell as `$FAL_KEY`. Check with `slopguard doctor` (it prints only set/not set).
2. **fal MCP connector**: if the plugin's `fal` MCP server is connected for this bot (the user puts the key in
   Integrations → Manage MCP servers → fal → Advanced → Access token), you may use its tools to search models,
   read schemas and pricing. Run paid generations through `slopguard fal run` anyway, so the budget and the log
   in `.slopguard/fal-calls.jsonl` stay accurate. If you do run one through MCP, append it to that log yourself.

## Before any paid call

1. The shot exists in `ledger.csv` with an idea, and no higher rung of the real-material ladder can show it
   (see `antislop-video-director`).
2. Pick the endpoint from [references/fal-models.md](references/fal-models.md). Verify it still exists and read
   its input schema on its fal model page (`https://fal.ai/models/<endpoint>/api`), via the fal MCP, or with
   `genmedia schema <endpoint> --json` if the genmedia CLI is installed. Do not invent endpoint ids or parameters.
3. Write the generation plan as `gen/plan.json` (endpoint, purpose, count, unit, quantity, unit price you read on
   the model page, price source) and render it with `slopguard fal plan gen/plan.json --out GENERATION_PLAN.md`.
   It totals the cost, checks the project's call budget, and refuses to look complete while a price is missing.
   Cheap drafts first (fast image model, low resolution, short duration), finals only for chosen shots.
4. Show the plan and get an explicit yes in chat. The project budget is `slopguard.json` → `fal.max_calls`
   (default 12). Raising it needs the user's yes too.

## Running

```bash
# input.json holds the model input; local paths in *_url fields are uploaded automatically
slopguard fal run fal-ai/nano-banana-pro --input gen/shot04-key.json --out gen/shot04 --label shot04 --confirm
slopguard fal run <endpoint> --arg prompt="..." --arg aspect_ratio='"9:16"' --out gen/x --confirm
slopguard fal budget            # calls used / allowed in this project
slopguard fal upload assets/ref.png   # returns a URL usable as image_url
slopguard fal result --response-url <url>   # recover a result after a timeout
```

`--confirm` is your statement that this exact call is inside the approved plan. Outputs land in `--out`
together with the full result JSON (seed, model, input) so a good result can be reproduced or extended.

## Prompts that do not produce slop

- Describe the specific subject, material, place, time of day, lens and light from `SPEC.md`, not adjectives
  ("cinematic, stunning, 8k, trending" are noise).
- One subject and one action per clip; 3-6 s clips cut together beat one long drifting clip.
- Keep identity consistent with a reference image (edit/reference-to-video endpoints) rather than re-describing.
- Never put readable text in a generated image or clip; add text as a code-drawn layer.
- Never generate real, identifiable people, real brands' products as if real, documents, screenshots or news
  footage. Never clone a voice without the owner's written consent.

## After each call

Look at it before using it: make a contact sheet for clips (`slopguard sheet clip.mp4 --out gen/x/sheet`).
Reject: extra or fused fingers, melting faces, warped text, objects morphing, wrong physics, flicker, the
wrong object. Note rejected calls in `project.md` so the same prompt is not paid for twice. Record kept
outputs in `ledger.csv` with `source_type=generated`, the endpoint and the request id in `source`.

## Voice and transcripts

- Prefer the user's own recorded voice. With TTS, choose one named voice for the channel and keep it;
  do not add style adjectives to the voice prompt; disclose synthetic voice where the platform asks.
- Transcribe the final narration with a word-level model (for example ElevenLabs Scribe on fal) and cut and
  caption on word boundaries. Cache transcripts; never re-transcribe an unchanged file.
