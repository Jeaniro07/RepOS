// Package lexicon holds the phrase lists for narration/script lint, English and Indonesian.
//
// Each entry: regex, weight, category, hint. Weight 3 = strong tell, 2 = common tell,
// 1 = weak tell (only matters in bulk). Written for spoken narration in short/long-form
// video, not essays. A single hit is a note; density is the signal. Extend per channel in
// slopguard.json ("lexicon": {"extra": [["regex", 2, "category", "hint"]]}).
// Kept identical to toolkit/slopguard/lexicon.py.
package lexicon

// Categories
const (
	Filler    = "filler-opener"
	Hype      = "hype-word"
	Cliche    = "cliche"
	Bait      = "engagement-bait"
	Hedge     = "hedge"
	Frame     = "contrast-frame"
	Signpost  = "signpost"
	Clickbait = "clickbait"
)

// Entry is one stock phrase.
type Entry struct {
	Pattern  string
	Weight   int
	Category string
	Hint     string
}

var EN = []Entry{
	// Generic openers / closers
	{`\bin today'?s (fast[- ]paced|digital|modern|ever[- ]changing) (world|age|landscape)\b`, 3, Filler, "Open on the specific thing, not the era."},
	{`\bin a world where\b`, 3, Filler, "Start with the event or the person instead."},
	{`\bhave you ever wondered\b`, 2, Filler, "Ask the real question directly, or show the answer first."},
	{`\blet'?s (dive|jump) (right )?in(to)?\b`, 3, Signpost, "Cut it; just start."},
	{`\bwithout further ado\b`, 3, Signpost, "Cut it."},
	{`\bbuckle up\b`, 2, Signpost, "Cut it."},
	{`\bhere'?s the (thing|kicker|catch)\b`, 2, Signpost, "State the thing."},
	{`\bin conclusion\b|\bto sum (it )?up\b|\bin summary\b`, 2, Signpost, "End on the payoff, not on a label."},
	{`\bat the end of the day\b`, 2, Cliche, "Say what actually happens."},
	{`\bit'?s (important|worth|crucial) (to note|noting|to remember)\b`, 3, Hedge, "If it matters, just say it."},
	{`\bit goes without saying\b`, 2, Hedge, "Then don't say it, or say it plainly."},
	// Hype / LLM-favourite words
	{`\bdelv(e|es|ing)\b`, 3, Hype, "Use 'look at', 'dig into', or the verb you mean."},
	{`\btapestry\b`, 3, Hype, "Name the actual parts."},
	{`\btestament to\b`, 3, Hype, "Say what it proves."},
	{`\b(game[- ]?changer|game[- ]?changing)\b`, 3, Hype, "Say what changes, with a number."},
	{`\bunlock(s|ing)? (the )?(power|potential|secrets?)\b`, 3, Hype, "Say what the viewer can now do."},
	{`\b(revolutioni[sz]e|revolutionary)\b`, 2, Hype, "Describe the change concretely."},
	{`\bcutting[- ]edge\b|\bstate[- ]of[- ]the[- ]art\b`, 2, Hype, "Name the feature."},
	{`\bseamless(ly)?\b`, 2, Hype, "Show it working instead."},
	{`\bel(e|a)vat(e|es|ing)\b`, 2, Hype, "Say what improves."},
	{`\bharness(ing)? the\b`, 2, Hype, "Use 'use'."},
	{`\bnavigat(e|ing) the (complexities|world|landscape)\b`, 3, Hype, "Say what the viewer does."},
	{`\b(ever[- ]evolving|ever[- ]changing) (landscape|world)\b`, 3, Cliche, "Name what changed."},
	{`\b(realm|landscape) of\b`, 2, Hype, "Name the field."},
	{`\b(embark|embarking) on (a|this) journey\b`, 3, Cliche, "Say what you're doing."},
	{`\b(vibrant|bustling|nestled)\b`, 1, Hype, "Describe what you see or hear."},
	{`\b(pivotal|paramount|multifaceted|myriad)\b`, 1, Hype, "Plainer word."},
	{`\bplays? an? (crucial|pivotal|vital|key|important) role\b`, 2, Cliche, "Say what it does."},
	{`\bit'?s worth mentioning\b|\bneedless to say\b`, 2, Hedge, "Just say it."},
	{`\bmore than just an?\b`, 2, Frame, "Say what it actually is."},
	{`\bmoreover\b|\bfurthermore\b|\badditionally\b`, 1, Signpost, "Spoken English rarely uses these."},
	{`\bmind[- ]?blowing\b|\bjaw[- ]?dropping\b`, 2, Hype, "Let the fact do it."},
	{`\bthe (secret|truth) (nobody|no one) (tells|talks about)\b`, 3, Clickbait, "Only if it is actually a secret, with a source."},
	{`\byou won'?t believe\b`, 3, Clickbait, "Show it."},
	{`\b(this|that) changes everything\b`, 3, Clickbait, "Say what it changes."},
	// Contrast frames
	{`\bit'?s not (just )?about [^.?!]{1,40}, it'?s about\b`, 3, Frame, "State the claim once."},
	{`\bnot (just|only|merely) [^.?!]{1,40},? but (also )?\b`, 2, Frame, "One claim, said plainly."},
	{`\bisn'?t just [^.?!]{1,30}[-—–,]? it'?s\b`, 2, Frame, "One claim, said plainly."},
	{`\bwhether you'?re an? [^.?!]{1,30} or an? \b`, 2, Cliche, "Pick the one viewer this is for."},
	// Engagement bait
	{`\b(smash|hit) (that|the) (like|subscribe)\b`, 3, Bait, "Earn it; one plain ask at most."},
	{`\bdon'?t forget to (like|subscribe|comment|share)\b`, 2, Bait, "One plain ask at most, at the end."},
	{`\bcomment (below|down below)\b|\blet me know in the comments\b`, 2, Bait, "Only with a real question tied to the video."},
	{`\bstay tuned\b|\bwatch (un)?till the end\b|\bwait for it\b`, 2, Bait, "Deliver early instead of withholding."},
	{`\b(follow|subscribe) for (more|part 2)\b`, 1, Bait, "Fine once; never as the hook."},
}

var ID = []Entry{
	// Pembuka / penutup generik
	{`\bdi (era|zaman) (digital|modern|serba cepat|sekarang)( ini)?\b`, 3, Filler, "Buka dengan hal spesifik, bukan zamannya."},
	{`\bdi dunia yang (serba cepat|terus berubah)\b`, 3, Filler, "Buka dengan kejadian atau orangnya."},
	{`\bpernahkah (kamu|anda) (bertanya|berpikir)\b`, 2, Filler, "Langsung ke pertanyaan aslinya, atau tunjukkan jawabannya dulu."},
	{`\bmari kita (selami|bahas|kupas|bedah)\b`, 3, Signpost, "Hapus; langsung mulai."},
	{`\btanpa basa[- ]basi( lagi)?\b`, 3, Signpost, "Hapus."},
	{`\bkesimpulannya\b|\bsebagai kesimpulan\b|\bdapat disimpulkan\b`, 2, Signpost, "Tutup dengan payoff, bukan label."},
	{`\bpada akhirnya\b|\bujung[- ]ujungnya\b`, 1, Cliche, "Katakan apa yang terjadi."},
	{`\btidak dapat dipungkiri\b|\btak bisa dipungkiri\b`, 3, Hedge, "Kalau benar, katakan saja dengan sumbernya."},
	{`\bperlu (diingat|dicatat|diketahui) bahwa\b|\bpenting untuk (diingat|dicatat|diketahui)\b`, 3, Hedge, "Kalau penting, langsung katakan."},
	{`\bsangat (penting|krusial) untuk\b`, 2, Hedge, "Tunjukkan kenapa penting."},
	{`\bseperti yang kita ketahui( bersama)?\b|\bsebagaimana kita tahu\b`, 2, Hedge, "Hapus."},
	{`\bpatut dicatat bahwa\b|\bsebagaimana diketahui( bersama)?\b`, 3, Hedge, "Hapus; langsung ke isinya."},
	{`\bmemainkan peran (yang )?(penting|krusial|kunci|vital)\b`, 2, Cliche, "Sebut apa yang dilakukannya."},
	{`\bdalam dunia yang (terus )?(berkembang|berubah)\b`, 3, Filler, "Buka dengan hal spesifik."},
	{`\btak hanya itu\b|\bbukan cuma itu\b`, 1, Signpost, "Langsung ke poin berikutnya."},
	{`\blebih dari sekadar\b`, 2, Frame, "Katakan apa itu sebenarnya."},
	// Kata hype
	{`\bgame ?changer\b|\bmengubah permainan\b`, 3, Hype, "Sebut apa yang berubah, pakai angka."},
	{`\b(revolusioner|merevolusi)\b`, 2, Hype, "Jelaskan perubahannya secara konkret."},
	{`\bmembuka (potensi|rahasia|kekuatan)\b`, 3, Hype, "Sebut apa yang sekarang bisa dilakukan penonton."},
	{`\bmenyelami\b`, 3, Hype, "Pakai 'melihat', 'membahas', atau kata kerja yang dimaksud."},
	{`\b(solusi|cara) (terbaik|paling ampuh|jitu)\b`, 2, Hype, "Buktikan, jangan klaim."},
	{`\bmutakhir\b|\bterdepan\b|\bcanggih\b`, 1, Hype, "Sebut fiturnya."},
	{`\bmeningkatkan (kualitas|level) (hidup|kamu)\b|\bnaik level\b`, 2, Hype, "Sebut apa yang membaik."},
	{`\b(lanskap|ranah) (digital|bisnis|teknologi)\b`, 2, Hype, "Sebut bidangnya."},
	{`\bperjalanan (yang )?(luar biasa|menakjubkan)\b`, 2, Cliche, "Ceritakan apa yang terjadi."},
	{`\bluar biasa\b|\bmenakjubkan\b|\bspektakuler\b`, 1, Hype, "Biar faktanya yang bicara."},
	{`\bselain itu\b|\blebih lanjut\b|\badapun\b`, 1, Signpost, "Bahasa lisan jarang memakai ini."},
	// Clickbait
	{`\brahasia yang (tidak|jarang) (banyak )?(orang )?(tahu|diketahui)\b`, 3, Clickbait, "Hanya kalau memang rahasia, dengan sumber."},
	{`\b(kamu|anda) (tidak|nggak|gak) akan percaya\b`, 3, Clickbait, "Tunjukkan saja."},
	{`\bini (akan )?mengubah segalanya\b`, 3, Clickbait, "Sebut apa yang berubah."},
	{`\bwajib (tahu|nonton)\b|\bsimak sampai (habis|akhir)\b|\btonton sampai (habis|akhir)\b`, 2, Bait, "Beri payoff di awal, jangan ditahan."},
	{`\bsiapa sangka\b|\bternyata oh ternyata\b`, 2, Cliche, "Tunjukkan kejutan, jangan diumumkan."},
	{`\bviral\b`, 1, Clickbait, "Jangan menjanjikan viral."},
	// Kerangka kontras
	{`\bbukan (hanya|sekadar|cuma) [^.?!]{1,40},? (tetapi|tapi|melainkan) (juga )?\b`, 2, Frame, "Satu klaim, sederhana."},
	{`\bini bukan (soal|tentang) [^.?!]{1,40}, (ini|tapi) (soal|tentang)\b`, 3, Frame, "Nyatakan klaimnya sekali."},
	// Pancingan interaksi
	{`\bjangan lupa (like|subscribe|komen|share|follow)\b`, 2, Bait, "Maksimal satu ajakan polos di akhir."},
	{`\blike,? (comment|komen),? (dan|and) (subscribe|share)\b`, 3, Bait, "Maksimal satu ajakan polos di akhir."},
	{`\btulis di kolom komentar\b|\bkomen di bawah\b`, 2, Bait, "Hanya dengan pertanyaan asli yang terkait video."},
	{`\bstay tuned\b|\btunggu sampai akhir\b`, 2, Bait, "Beri payoff lebih awal."},
}

// Words that make a sentence a factual claim needing a citation.
var ClaimCuesEN = []string{
	`\b(studies|research|scientists|experts|data|surveys?) (show|shows|found|say|says|suggest)\b`,
	`\baccording to\b`,
	`\b(proven|statistically)\b`,
	`\b\d+(\.\d+)?\s?%`,
	`\b\d+(\.\d+)?\s?(percent|million|billion|trillion)\b`,
	`[$€£¥]\s?\d`,
	`\b\d+(\.\d+)?\s?(x|times) (more|less|faster|slower|higher|lower|cheaper)\b`,
}

var ClaimCuesID = []string{
	`\b(penelitian|studi|riset|survei|data|ilmuwan|para ahli|pakar) (menunjukkan|membuktikan|menemukan|mengatakan|menyebut)\b`,
	`\bmenurut (penelitian|studi|data|survei|laporan|para ahli)\b`,
	`\b(terbukti|secara ilmiah|secara statistik)\b`,
	`\b\d+([.,]\d+)?\s?%`,
	`\b\d+([.,]\d+)?\s?(persen|ribu|juta|miliar|triliun)\b`,
	`\brp\.?\s?\d`,
	`\b\d+([.,]\d+)?\s?kali (lipat|lebih)\b`,
}

func set(words ...string) map[string]bool {
	m := make(map[string]bool, len(words))
	for _, w := range words {
		m[w] = true
	}
	return m
}

var FunctionWordsEN = set("the", "and", "is", "to", "of", "you", "that", "it", "for", "this", "are", "with", "what", "your")
var FunctionWordsID = set("yang", "dan", "di", "ini", "itu", "untuk", "dengan", "tidak", "kita", "kamu", "ada", "akan", "dari", "bisa", "atau", "juga", "karena")

// SpeakingWPM is the typical spoken narration pace, words per minute.
var SpeakingWPM = map[string]float64{"en": 155, "id": 140}

// Generic hook openers checked on the first sentence only.
var GenericHookEN = []string{
	`^(hey|hi|hello)( guys| everyone| there)?\b`,
	`^(welcome|welcome back) to\b`,
	`^(today|in this video),? (we|i)('ll| will| are going to| am going to)\b`,
	`^have you ever\b`,
	`^did you know\b`,
	`^in today'?s\b`,
	`^imagine\b`,
}

var GenericHookID = []string{
	`^(halo|hai|hi)( guys| semuanya| teman[- ]teman| sobat)?\b`,
	`^(selamat datang|kembali lagi) (di|ke|dengan)\b`,
	`^(di video ini|hari ini),? (kita|aku|saya) (akan|mau)\b`,
	`^pernahkah\b`,
	`^tahukah (kamu|anda)\b`,
	`^di (era|zaman)\b`,
	`^bayangkan\b`,
}
