"""Phrase lists for narration/script lint, English and Indonesian.

Each entry: (regex, weight, category, hint). Weight 3 = strong tell,
2 = common tell, 1 = weak tell (only matters in bulk).

These lists are written for spoken narration in short/long-form video,
not for essays. They are deliberately conservative: a single hit is a
note, density is the signal. Extend them per channel in slopguard.json
("lexicon": {"extra": [["regex", 2, "category", "hint"]]}).
"""

from __future__ import annotations

# Categories
FILLER = "filler-opener"
HYPE = "hype-word"
CLICHE = "cliche"
BAIT = "engagement-bait"
HEDGE = "hedge"
FRAME = "contrast-frame"
SIGNPOST = "signpost"
CLICKBAIT = "clickbait"

EN = [
    # Generic openers / closers
    (r"\bin today'?s (fast[- ]paced|digital|modern|ever[- ]changing) (world|age|landscape)\b", 3, FILLER, "Open on the specific thing, not the era."),
    (r"\bin a world where\b", 3, FILLER, "Start with the event or the person instead."),
    (r"\bhave you ever wondered\b", 2, FILLER, "Ask the real question directly, or show the answer first."),
    (r"\blet'?s (dive|jump) (right )?in(to)?\b", 3, SIGNPOST, "Cut it; just start."),
    (r"\bwithout further ado\b", 3, SIGNPOST, "Cut it."),
    (r"\bbuckle up\b", 2, SIGNPOST, "Cut it."),
    (r"\bhere'?s the (thing|kicker|catch)\b", 2, SIGNPOST, "State the thing."),
    (r"\bin conclusion\b|\bto sum (it )?up\b|\bin summary\b", 2, SIGNPOST, "End on the payoff, not on a label."),
    (r"\bat the end of the day\b", 2, CLICHE, "Say what actually happens."),
    (r"\bit'?s (important|worth|crucial) (to note|noting|to remember)\b", 3, HEDGE, "If it matters, just say it."),
    (r"\bit goes without saying\b", 2, HEDGE, "Then don't say it, or say it plainly."),
    # Hype / LLM-favourite words
    (r"\bdelv(e|es|ing)\b", 3, HYPE, "Use 'look at', 'dig into', or the verb you mean."),
    (r"\btapestry\b", 3, HYPE, "Name the actual parts."),
    (r"\btestament to\b", 3, HYPE, "Say what it proves."),
    (r"\b(game[- ]?changer|game[- ]?changing)\b", 3, HYPE, "Say what changes, with a number."),
    (r"\bunlock(s|ing)? (the )?(power|potential|secrets?)\b", 3, HYPE, "Say what the viewer can now do."),
    (r"\b(revolutioni[sz]e|revolutionary)\b", 2, HYPE, "Describe the change concretely."),
    (r"\bcutting[- ]edge\b|\bstate[- ]of[- ]the[- ]art\b", 2, HYPE, "Name the feature."),
    (r"\bseamless(ly)?\b", 2, HYPE, "Show it working instead."),
    (r"\bel(e|a)vat(e|es|ing)\b", 2, HYPE, "Say what improves."),
    (r"\bharness(ing)? the\b", 2, HYPE, "Use 'use'."),
    (r"\bnavigat(e|ing) the (complexities|world|landscape)\b", 3, HYPE, "Say what the viewer does."),
    (r"\b(ever[- ]evolving|ever[- ]changing) (landscape|world)\b", 3, CLICHE, "Name what changed."),
    (r"\b(realm|landscape) of\b", 2, HYPE, "Name the field."),
    (r"\b(embark|embarking) on (a|this) journey\b", 3, CLICHE, "Say what you're doing."),
    (r"\b(vibrant|bustling|nestled)\b", 1, HYPE, "Describe what you see or hear."),
    (r"\b(pivotal|paramount|multifaceted|myriad)\b", 1, HYPE, "Plainer word."),
    (r"\bplays? an? (crucial|pivotal|vital|key|important) role\b", 2, CLICHE, "Say what it does."),
    (r"\bit'?s worth mentioning\b|\bneedless to say\b", 2, HEDGE, "Just say it."),
    (r"\bmore than just an?\b", 2, FRAME, "Say what it actually is."),
    (r"\bmoreover\b|\bfurthermore\b|\badditionally\b", 1, SIGNPOST, "Spoken English rarely uses these."),
    (r"\bmind[- ]?blowing\b|\bjaw[- ]?dropping\b", 2, HYPE, "Let the fact do it."),
    (r"\bthe (secret|truth) (nobody|no one) (tells|talks about)\b", 3, CLICKBAIT, "Only if it is actually a secret, with a source."),
    (r"\byou won'?t believe\b", 3, CLICKBAIT, "Show it."),
    (r"\b(this|that) changes everything\b", 3, CLICKBAIT, "Say what it changes."),
    # Contrast frames
    (r"\bit'?s not (just )?about [^.?!]{1,40}, it'?s about\b", 3, FRAME, "State the claim once."),
    (r"\bnot (just|only|merely) [^.?!]{1,40},? but (also )?\b", 2, FRAME, "One claim, said plainly."),
    (r"\bisn'?t just [^.?!]{1,30}[-—–,]? it'?s\b", 2, FRAME, "One claim, said plainly."),
    (r"\bwhether you'?re an? [^.?!]{1,30} or an? \b", 2, CLICHE, "Pick the one viewer this is for."),
    # Engagement bait
    (r"\b(smash|hit) (that|the) (like|subscribe)\b", 3, BAIT, "Earn it; one plain ask at most."),
    (r"\bdon'?t forget to (like|subscribe|comment|share)\b", 2, BAIT, "One plain ask at most, at the end."),
    (r"\bcomment (below|down below)\b|\blet me know in the comments\b", 2, BAIT, "Only with a real question tied to the video."),
    (r"\bstay tuned\b|\bwatch (un)?till the end\b|\bwait for it\b", 2, BAIT, "Deliver early instead of withholding."),
    (r"\b(follow|subscribe) for (more|part 2)\b", 1, BAIT, "Fine once; never as the hook."),
]

ID = [
    # Pembuka / penutup generik
    (r"\bdi (era|zaman) (digital|modern|serba cepat|sekarang)( ini)?\b", 3, FILLER, "Buka dengan hal spesifik, bukan zamannya."),
    (r"\bdi dunia yang (serba cepat|terus berubah)\b", 3, FILLER, "Buka dengan kejadian atau orangnya."),
    (r"\bpernahkah (kamu|anda) (bertanya|berpikir)\b", 2, FILLER, "Langsung ke pertanyaan aslinya, atau tunjukkan jawabannya dulu."),
    (r"\bmari kita (selami|bahas|kupas|bedah)\b", 3, SIGNPOST, "Hapus; langsung mulai."),
    (r"\btanpa basa[- ]basi( lagi)?\b", 3, SIGNPOST, "Hapus."),
    (r"\bkesimpulannya\b|\bsebagai kesimpulan\b|\bdapat disimpulkan\b", 2, SIGNPOST, "Tutup dengan payoff, bukan label."),
    (r"\bpada akhirnya\b|\bujung[- ]ujungnya\b", 1, CLICHE, "Katakan apa yang terjadi."),
    (r"\btidak dapat dipungkiri\b|\btak bisa dipungkiri\b", 3, HEDGE, "Kalau benar, katakan saja dengan sumbernya."),
    (r"\bperlu (diingat|dicatat|diketahui) bahwa\b|\bpenting untuk (diingat|dicatat|diketahui)\b", 3, HEDGE, "Kalau penting, langsung katakan."),
    (r"\bsangat (penting|krusial) untuk\b", 2, HEDGE, "Tunjukkan kenapa penting."),
    (r"\bseperti yang kita ketahui( bersama)?\b|\bsebagaimana kita tahu\b", 2, HEDGE, "Hapus."),
    (r"\bpatut dicatat bahwa\b|\bsebagaimana diketahui( bersama)?\b", 3, HEDGE, "Hapus; langsung ke isinya."),
    (r"\bmemainkan peran (yang )?(penting|krusial|kunci|vital)\b", 2, CLICHE, "Sebut apa yang dilakukannya."),
    (r"\bdalam dunia yang (terus )?(berkembang|berubah)\b", 3, FILLER, "Buka dengan hal spesifik."),
    (r"\btak hanya itu\b|\bbukan cuma itu\b", 1, SIGNPOST, "Langsung ke poin berikutnya."),
    (r"\blebih dari sekadar\b", 2, FRAME, "Katakan apa itu sebenarnya."),
    # Kata hype
    (r"\bgame ?changer\b|\bmengubah permainan\b", 3, HYPE, "Sebut apa yang berubah, pakai angka."),
    (r"\b(revolusioner|merevolusi)\b", 2, HYPE, "Jelaskan perubahannya secara konkret."),
    (r"\bmembuka (potensi|rahasia|kekuatan)\b", 3, HYPE, "Sebut apa yang sekarang bisa dilakukan penonton."),
    (r"\bmenyelami\b", 3, HYPE, "Pakai 'melihat', 'membahas', atau kata kerja yang dimaksud."),
    (r"\b(solusi|cara) (terbaik|paling ampuh|jitu)\b", 2, HYPE, "Buktikan, jangan klaim."),
    (r"\bmutakhir\b|\bterdepan\b|\bcanggih\b", 1, HYPE, "Sebut fiturnya."),
    (r"\bmeningkatkan (kualitas|level) (hidup|kamu)\b|\bnaik level\b", 2, HYPE, "Sebut apa yang membaik."),
    (r"\b(lanskap|ranah) (digital|bisnis|teknologi)\b", 2, HYPE, "Sebut bidangnya."),
    (r"\bperjalanan (yang )?(luar biasa|menakjubkan)\b", 2, CLICHE, "Ceritakan apa yang terjadi."),
    (r"\bluar biasa\b|\bmenakjubkan\b|\bspektakuler\b", 1, HYPE, "Biar faktanya yang bicara."),
    (r"\bselain itu\b|\blebih lanjut\b|\badapun\b", 1, SIGNPOST, "Bahasa lisan jarang memakai ini."),
    # Clickbait
    (r"\brahasia yang (tidak|jarang) (banyak )?(orang )?(tahu|diketahui)\b", 3, CLICKBAIT, "Hanya kalau memang rahasia, dengan sumber."),
    (r"\b(kamu|anda) (tidak|nggak|gak) akan percaya\b", 3, CLICKBAIT, "Tunjukkan saja."),
    (r"\bini (akan )?mengubah segalanya\b", 3, CLICKBAIT, "Sebut apa yang berubah."),
    (r"\bwajib (tahu|nonton)\b|\bsimak sampai (habis|akhir)\b|\btonton sampai (habis|akhir)\b", 2, BAIT, "Beri payoff di awal, jangan ditahan."),
    (r"\bsiapa sangka\b|\bternyata oh ternyata\b", 2, CLICHE, "Tunjukkan kejutan, jangan diumumkan."),
    (r"\bviral\b", 1, CLICKBAIT, "Jangan menjanjikan viral."),
    # Kerangka kontras
    (r"\bbukan (hanya|sekadar|cuma) [^.?!]{1,40},? (tetapi|tapi|melainkan) (juga )?\b", 2, FRAME, "Satu klaim, sederhana."),
    (r"\bini bukan (soal|tentang) [^.?!]{1,40}, (ini|tapi) (soal|tentang)\b", 3, FRAME, "Nyatakan klaimnya sekali."),
    # Pancingan interaksi
    (r"\bjangan lupa (like|subscribe|komen|share|follow)\b", 2, BAIT, "Maksimal satu ajakan polos di akhir."),
    (r"\blike,? (comment|komen),? (dan|and) (subscribe|share)\b", 3, BAIT, "Maksimal satu ajakan polos di akhir."),
    (r"\btulis di kolom komentar\b|\bkomen di bawah\b", 2, BAIT, "Hanya dengan pertanyaan asli yang terkait video."),
    (r"\bstay tuned\b|\btunggu sampai akhir\b", 2, BAIT, "Beri payoff lebih awal."),
]

# Words that make a sentence a factual claim needing a citation.
CLAIM_CUES_EN = [
    r"\b(studies|research|scientists|experts|data|surveys?) (show|shows|found|say|says|suggest)\b",
    r"\baccording to\b",
    r"\b(proven|statistically)\b",
    r"\b\d+(\.\d+)?\s?%",
    r"\b\d+(\.\d+)?\s?(percent|million|billion|trillion)\b",
    r"[$€£¥]\s?\d",
    r"\b\d+(\.\d+)?\s?(x|times) (more|less|faster|slower|higher|lower|cheaper)\b",
]
CLAIM_CUES_ID = [
    r"\b(penelitian|studi|riset|survei|data|ilmuwan|para ahli|pakar) (menunjukkan|membuktikan|menemukan|mengatakan|menyebut)\b",
    r"\bmenurut (penelitian|studi|data|survei|laporan|para ahli)\b",
    r"\b(terbukti|secara ilmiah|secara statistik)\b",
    r"\b\d+([.,]\d+)?\s?%",
    r"\b\d+([.,]\d+)?\s?(persen|ribu|juta|miliar|triliun)\b",
    r"\brp\.?\s?\d",
    r"\b\d+([.,]\d+)?\s?kali (lipat|lebih)\b",
]

FUNCTION_WORDS_EN = {"the", "and", "is", "to", "of", "you", "that", "it", "for", "this", "are", "with", "what", "your"}
FUNCTION_WORDS_ID = {"yang", "dan", "di", "ini", "itu", "untuk", "dengan", "tidak", "kita", "kamu", "ada", "akan", "dari", "bisa", "atau", "juga", "karena"}

# Typical spoken narration pace, words per minute.
SPEAKING_WPM = {"en": 155, "id": 140}

# Generic hook openers checked on the first sentence only.
GENERIC_HOOK_EN = [
    r"^(hey|hi|hello)( guys| everyone| there)?\b",
    r"^(welcome|welcome back) to\b",
    r"^(today|in this video),? (we|i)('ll| will| are going to| am going to)\b",
    r"^have you ever\b",
    r"^did you know\b",
    r"^in today'?s\b",
    r"^imagine\b",
]
GENERIC_HOOK_ID = [
    r"^(halo|hai|hi)( guys| semuanya| teman[- ]teman| sobat)?\b",
    r"^(selamat datang|kembali lagi) (di|ke|dengan)\b",
    r"^(di video ini|hari ini),? (kita|aku|saya) (akan|mau)\b",
    r"^pernahkah\b",
    r"^tahukah (kamu|anda)\b",
    r"^di (era|zaman)\b",
    r"^bayangkan\b",
]
