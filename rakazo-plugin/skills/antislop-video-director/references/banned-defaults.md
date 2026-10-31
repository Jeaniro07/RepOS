# Defaults that read as generated

Copy the relevant lines into the BANNED line of `SPEC.md` before the first render. After the first render,
name every default that slipped in anyway (from this list or not), add it to BANNED, and fix it. The list
grows with every video. A banned default is allowed only when the brand's own material or the user's
reference uses it, and then only the way they use it.

Sources of this list: production rules in heygen-com/hyperframes (spec and review references),
Vincentwei1021/video-shotcraft (aesthetic rules), kaomei/stickman-video-director (autopilot QA),
browser-use/video-use (anti-patterns), Nutlope/hallmark (Floor), and our own QA gates.

## Picture

- A dark void (black or navy) with small elements floating in the middle of the frame.
- Glow, bloom, neon, lens flares, glowing orbs, decorative particles, light sweeps on everything.
- Purple-to-blue gradients, mesh gradients, glass cards.
- A slow Ken Burns zoom over a generated still standing in for a scene.
- Three cards in a row, KPI grids, a title over a dimmed screenshot.
- The logo docked in a corner for the whole video.
- Emoji used as icons; a pile of unrelated logos; icons that are not the thing being discussed.
- Generic stock b-roll (people typing, city timelapse, handshake) that does not explain the sentence.
- Generated people with the same face as every other generated video; plastic skin; hands with wrong fingers.
- Text inside generated images (it garbles); put real text in code-drawn layers instead.
- A hero object that fills less than 40% of the frame with nothing else to look at.
- A hand-drawn browser or phone frame faking a real product screen; capture the real screen instead.

## Motion

- Everything fades in and slides up; every scene enters the same way.
- Titles that keep drifting or scaling after they land; text that moves while it is being read.
- Breathing, floating or pulsing loops standing in for motion.
- Linear easing; uniform speed; all elements revealed at once.
- Whole-frame shake or zoom pulse on every beat (allowed at most three times in a film).
- Cuts every N seconds like a metronome; a transition effect on every cut.

## Sound

- Flat TTS read without pauses; the same voice every channel uses; voice sped up to fit.
- "Hype" stock music by default; music as loud as the voice.
- A whoosh on every transition, a pop on every word; sound effects not tied to anything visible.
- Silence holes from bad cuts; pops at segment boundaries (use 30 ms fades).
- Clipping; loudness far from -14 LUFS.

## Words

- "Halo guys, selamat datang kembali", "Di video ini kita akan", "Di era digital ini", "Have you ever wondered".
- "Rahasia yang tidak banyak orang tahu", "Kamu tidak akan percaya", "Ini mengubah segalanya".
- "Bukan hanya X, tetapi juga Y" said again and again; lists of three everywhere.
- Numbers without sources; "studies show"; "para ahli mengatakan".
- "Jangan lupa like, comment, dan subscribe" / "simak sampai habis" / "stay tuned".
- Promising virality or earnings.

## Captions

- Emoji in captions; every caption a different colour; captions jumping position.
- Captions faster than 20 characters per second; one-word flashes under 0.7 s for a whole video.
- Captions under the platform buttons or covering the face/product.
