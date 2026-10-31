---
name: antislop-script
description: Write or fix narration and on-screen copy for a video so it sounds like a person with something specific to say, not a template. Use when drafting a video script, voiceover, hook, caption copy or post description, or when the user asks to remove AI slop from a script. Every factual claim gets a source; lint with slopguard before showing it.
---

# Writing narration that is not slop

Narration is heard once, at speaking speed, by someone who can swipe away. Write it to be said.

## Before writing

- Read `BRIEF.md`: the one viewer, the one takeaway, the material, the sources. If the takeaway is not
  clear, ask; do not paper over it with adjectives.
- Collect the specifics first: names, numbers, places, dates, the actual steps, the actual result, the
  moment something went wrong. A script is built from specifics; adjectives are what is left when there
  are none.

## Rules

1. **Hook in one line, from the material.** The most specific, surprising true thing you have, or the result
   shown first. Never a greeting, the channel name, "in this video", the era ("di era digital ini"), or a
   question you could ask about any topic.
2. **One claim per sentence.** Short sentences for punches, longer ones to explain; vary the length on purpose.
3. **Source every fact.** Any number, percentage, money amount, ranking, study or "para ahli" gets `[n]`,
   and `[n]` is listed under `Sumber:` as `[n] title, publisher, date, URL`. Open each source and check it
   says what you claim. If you cannot, cut the claim or say it as your opinion ("menurut saya").
4. **Show, then say.** Write `[VISUAL: ...]` for what is on screen; let the picture carry what it can and
   cut the words it makes redundant.
5. **Plain spoken words.** No "selain itu", "adapun", "moreover", "delve", "game changer", "revolusioner",
   "membuka potensi". Say the verb you mean.
6. **No bait.** No "simak sampai habis", no "kamu tidak akan percaya", no "jangan lupa like, comment, dan
   subscribe". At most one plain ask at the end, tied to the video ("Kalau kamu coba, suhu berapa yang
   paling enak?").
7. **No fake balance or fake depth.** Drop "bukan hanya X, tetapi juga Y" unless the contrast is the point;
   drop lists of three that exist for rhythm; drop rhetorical question stacks.
8. **Fit the time.** About 140 words per minute in Indonesian, 155 in English. Too long? Cut words. Never ask
   the voice to speed up.
9. **Keep the user's voice.** If the user wrote copy or approved a recording, preserve it. Propose changes
   as a diff with reasons; do not silently rewrite.
10. **Never promise outcomes** (viral, rich, cured, guaranteed) and never invent testimonials.

## Loop

```bash
slopguard lint-script script.md              # uses slopguard.json for language, duration, extra phrases
```

Fix every FLOOR. Fix every REFLEX, or add a waiver with a real reason to `waivers.json`. Read it aloud
in your head at speaking pace once more, then show the user the script and the lint summary
(score, unsourced claims, what you waived and why).

Channel-specific phrases the user dislikes go into `slopguard.json` → `lexicon.extra` as
`["regex", weight, "category", "hint"]` so every future script is checked for them.

## On-screen text and post copy

- On-screen text is a few words that the voice does not repeat word for word.
- Post title/description: say what the video shows, specifically. No "WAJIB NONTON", no emoji chains, no
  hashtag walls (3-5 relevant tags at most). Note AI-generated parts honestly if the platform asks.
