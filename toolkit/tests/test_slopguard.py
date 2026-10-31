import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import helpers  # noqa: E402

from slopguard import captions, fal, ledger, project, textlint, videoqa  # noqa: E402
from slopguard.report import EXIT_CLEAN, EXIT_FLOOR, EXIT_REFLEX, apply_waivers  # noqa: E402


def gates(report):
    return {f.gate for f in report.findings}


SLOPPY_ID = """# Naskah
Halo guys, selamat datang kembali di channel kita! Di era digital ini, AI adalah game changer.
Tidak dapat dipungkiri bahwa 87% orang sudah memakai AI setiap hari.
Mari kita selami rahasia yang tidak banyak orang tahu!
Penelitian menunjukkan produktivitas naik 3 kali lipat. Simak sampai habis ya!
Jangan lupa like, comment, dan subscribe! 🚀🔥💯
"""

CLEAN_ID = """# Naskah
[VISUAL: tangan menuang kopi ke gelas ukur 250 ml]
Kopi saya selalu pahit, padahal bijinya mahal.
Ternyata masalahnya air.
Air mendidih 100 derajat mengekstrak terlalu banyak senyawa pahit [1].
Saya turunkan ke sekitar 92 derajat, tunggu satu menit setelah mendidih.
Hasilnya lebih manis, dan rasa cokelatnya keluar.
Coba besok pagi, cukup dengan termometer dapur.

Sumber:
[1] Specialty Coffee Association, Water Quality Handbook, 2018, https://sca.coffee
"""

SLOPPY_EN = """Hey guys, welcome back to the channel! In today's fast-paced world, it's important to note that AI is a game-changer.
Let's dive in. Studies show that 90% of creators will be replaced.
It's not just about tools, it's about the future. Don't forget to like and subscribe!
"""


class ScriptLint(unittest.TestCase):
    def test_sloppy_indonesian_blocked(self):
        r = textlint.lint_script(SLOPPY_ID, lang="auto", target_seconds=30)
        self.assertEqual(r.metrics["language"], "id")
        self.assertEqual(r.exit_code(), EXIT_FLOOR)
        g = gates(r)
        for gate in ("script.unsourced-claim", "script.generic-hook", "script.engagement-bait", "script.emoji-hashtag", "script.slop-density"):
            self.assertIn(gate, g)

    def test_no_duplicate_hits_across_languages(self):
        r = textlint.lint_script(SLOPPY_ID)
        hits = [f for f in r.findings if f.gate == "script.hype-word" and "game changer" in f.message.lower()]
        self.assertEqual(len(hits), 1)

    def test_clean_indonesian_passes(self):
        r = textlint.lint_script(CLEAN_ID, target_seconds=20)
        self.assertEqual(r.exit_code(), EXIT_CLEAN, r.to_markdown())

    def test_sloppy_english(self):
        r = textlint.lint_script(SLOPPY_EN)
        self.assertEqual(r.metrics["language"], "en")
        self.assertIn("script.unsourced-claim", gates(r))
        self.assertIn("script.contrast-frame", gates(r))

    def test_generic_script_flagged(self):
        text = " ".join([
            "Ada banyak hal yang bisa kamu lakukan untuk membuat hidup lebih baik setiap hari.",
            "Semua orang ingin merasa lebih bahagia dan lebih produktif dalam pekerjaan mereka.",
            "Kuncinya adalah konsisten dan tidak mudah menyerah ketika menghadapi tantangan.",
            "Mulailah dari hal kecil dan lakukan dengan sepenuh hati supaya hasilnya terasa.",
            "Percayalah bahwa usaha tidak akan mengkhianati hasil jika kamu terus berusaha.",
        ])
        r = textlint.lint_script(text, lang="id")
        self.assertIn("script.generic", gates(r))
        self.assertNotIn("script.generic", gates(textlint.lint_script(CLEAN_ID)))

    def test_new_indonesian_phrases(self):
        r = textlint.lint_script("Patut dicatat bahwa kopi memainkan peran penting dalam dunia yang terus berkembang.", lang="id")
        cats = {f.gate for f in r.findings}
        self.assertTrue({"script.hedge", "script.cliche", "script.filler-opener"} <= cats, cats)

    def test_dangling_citation(self):
        r = textlint.lint_script("Air 100 derajat terlalu panas untuk kopi [2].\n\nSumber:\n[1] contoh\n")
        self.assertIn("script.dangling-citation", gates(r))

    def test_crammed(self):
        text = " ".join(["Kalimat ini cukup panjang untuk mengisi waktu bicara."] * 40)
        r = textlint.lint_script(text, lang="id", target_seconds=15)
        self.assertIn("script.crammed", gates(r))

    def test_waiver_needs_reason_and_never_waives_floor(self):
        r = textlint.lint_script(SLOPPY_ID)
        apply_waivers(r, [{"gate": "script.generic-hook", "reason": "persona channel memang menyapa dulu"},
                          {"gate": "script.unsourced-claim", "reason": "saya yakin benar sekali"}])
        hook = [f for f in r.findings if f.gate == "script.generic-hook"][0]
        self.assertTrue(hook.waived)
        self.assertTrue(all(not f.waived for f in r.findings if f.gate == "script.unsourced-claim"))


SRT_BAD = """1
00:00:00,000 --> 00:00:00,400
HALO

2
00:00:00,300 --> 00:00:02,000
Ini adalah kalimat yang sangat panjang sekali untuk satu baris caption 🚀

3
00:00:02,000 --> 00:00:20,000
akhir
"""

VTT_OK = """WEBVTT

00:00.000 --> 00:01.800
Kopi saya selalu pahit,

00:01.900 --> 00:03.600
padahal bijinya mahal.
"""


class Captions(unittest.TestCase):
    def test_language_reading_speed_gap_and_short(self):
        srt = "1\n00:00:00,000 --> 00:00:01,000\nIni kalimat yang cukup cepat\n\n2\n00:00:01,020 --> 00:00:01,780\nlagi\n"
        r_id = captions.check_captions(srt, lang="id")
        r_en = captions.check_captions(srt, lang="en")
        self.assertIn("captions.reading-speed", gates(r_id))  # 24 chars/s > 17 (Indonesian)
        self.assertIn("captions.reading-speed", gates(r_en))  # > 20 (English)
        self.assertIn("captions.gap", gates(r_id))
        self.assertIn("captions.short", gates(r_id))
        srt2 = "1\n00:00:00,000 --> 00:00:02,000\nKopi saya pahit sekali\n"
        self.assertNotIn("captions.reading-speed", gates(captions.check_captions(srt2, lang="id")))  # ~9.5 cps

    def test_near_cut(self):
        cues = captions.parse_captions("1\n00:00:01,000 --> 00:00:02,850\nhalo dunia\n")
        found = captions.near_cut_findings(cues, [3.0], fps=30)
        self.assertEqual([f.gate for f in found], ["captions.near-cut"])  # ends 150 ms before the cut
        self.assertEqual(captions.near_cut_findings(cues, [2.9], fps=30), [])  # within 2 frames: snapped
        self.assertEqual(captions.near_cut_findings(cues, [5.0], fps=30), [])

    def test_bad(self):
        r = captions.check_captions(SRT_BAD, video_duration=16.0)
        g = gates(r)
        for gate in ("captions.overlap", "captions.beyond-end", "captions.flash", "captions.line-length", "captions.reading-speed", "captions.emoji"):
            self.assertIn(gate, g)
        self.assertEqual(r.exit_code(), EXIT_FLOOR)

    def test_vtt_ok(self):
        r = captions.check_captions(VTT_OK, video_duration=4.0)
        self.assertEqual(len(captions.parse_captions(VTT_OK)), 2)
        self.assertEqual(r.exit_code(), EXIT_CLEAN, r.to_markdown())


LEDGER = """shot,start,end,narration,idea,visual,source_type,source,license,real_person,notes
1,0,3,Kopi saya pahit,masalahnya terlihat,tuang kopi close-up,footage,assets/pour.mp4,own recording,no,
2,3,6,Ternyata airnya,penyebabnya air,termometer 100,code,,,no,
3,6,9,,,AI barista smiling,generated,fal-ai/x,,yes,
4,9,12,lagu,,,stock,,,no,
"""


class Ledger(unittest.TestCase):
    def test_ledger(self):
        r = ledger.check_ledger(LEDGER)
        g = gates(r)
        self.assertIn("ledger.synthetic-real-person", g)
        self.assertIn("ledger.no-source", g)
        self.assertIn("ledger.no-license", g)
        self.assertIn("ledger.no-idea", g)
        self.assertEqual(r.exit_code(), EXIT_FLOOR)


class Project(unittest.TestCase):
    def test_init_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            first = project.init_project(d, "Tes", "vertical", 30, "id", 5)
            self.assertTrue(any(p.endswith("SPEC.md") for p in first))
            with open(os.path.join(d, "script.md"), "w") as fh:
                fh.write("punya pengguna")
            second = project.init_project(d, "Tes")
            self.assertEqual(second, [])
            with open(os.path.join(d, "script.md")) as fh:
                self.assertEqual(fh.read(), "punya pengguna")
            cfg = project.load_config(os.path.join(d, "edit"))
            self.assertEqual(cfg["fal"]["max_calls"], 5)


@unittest.skipUnless(helpers.have_ffmpeg(), "ffmpeg not installed")
class VideoQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="slopguard-test-")
        cls.sloppy = helpers.make_sloppy(os.path.join(cls.tmp, "sloppy.mp4"))
        cls.clean = helpers.make_clean(os.path.join(cls.tmp, "clean.mp4"))
        cls.metro = helpers.make_metronomic(os.path.join(cls.tmp, "metro.mp4"))

    def test_sloppy(self):
        r, p, pic = videoqa.qa_video(self.sloppy, target="540x960")
        g = gates(r)
        for gate in ("audio.clipping", "audio.dead-air", "picture.frozen", "picture.first-frame"):
            self.assertIn(gate, g)
        self.assertEqual(r.exit_code(), EXIT_FLOOR)

    def test_clean(self):
        r, p, pic = videoqa.qa_video(self.clean, target="540x960")
        g = gates(r) - {"video.low-res"}  # tests render small on purpose
        self.assertFalse(g & {"audio.clipping", "audio.dead-air", "picture.frozen", "picture.black", "edit.metronomic", "audio.loudness"}, r.to_markdown())
        self.assertGreaterEqual(len(pic.cuts), 3)

    def test_metronomic(self):
        r, p, pic = videoqa.qa_video(self.metro, target="540x960")
        self.assertIn("edit.metronomic", gates(r))

    def test_wrong_aspect_is_floor(self):
        r, p, pic = videoqa.qa_video(self.clean, target="landscape")
        sizes = [f for f in r.findings if f.gate == "video.size"]
        self.assertEqual(sizes[0].tier, "FLOOR")

    def test_flicker_detected_only_on_flicker(self):
        flick = helpers.make_flicker(os.path.join(self.tmp, "flicker.mp4"))
        r, p, pic = videoqa.qa_video(flick, target="540x960")
        self.assertIn("picture.flicker", gates(r))
        for clean in (self.clean, self.metro, self.sloppy):
            r2, _, _ = videoqa.qa_video(clean, target="540x960")
            self.assertNotIn("picture.flicker", gates(r2), clean)

    def test_safe_zone_sheet_for_vertical(self):
        from slopguard import sheet
        out = sheet.safe_zone_sheet(self.clean, os.path.join(self.tmp, "sz"), 16.0)
        self.assertTrue(out and os.path.getsize(out) > 1000)

    def test_ffmpeg_only_probe(self):
        os.environ["SLOPGUARD_FFPROBE"] = "none"
        try:
            from slopguard import media

            p = media.probe(self.clean)
            self.assertEqual((p.width, p.height), (540, 960))
            self.assertTrue(p.has_audio)
            self.assertAlmostEqual(p.duration, 16.0, delta=0.2)
        finally:
            del os.environ["SLOPGUARD_FFPROBE"]


class _FakeFal(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        _FakeFal.calls.append(("POST", self.path, self.headers.get("Authorization"), body))
        base = f"http://127.0.0.1:{self.server.server_port}"
        if self.path.startswith("/storage/upload/initiate"):
            return self._send({"upload_url": base + "/put/x", "file_url": base + "/files/x.png"})
        self._send({"request_id": "req-123456789", "status_url": base + "/q/requests/req/status", "response_url": base + "/q/requests/req"})

    def do_PUT(self):
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        _FakeFal.calls.append(("PUT", self.path, self.headers.get("Authorization"), b""))
        self._send({})

    def do_GET(self):
        _FakeFal.calls.append(("GET", self.path, self.headers.get("Authorization"), b""))
        base = f"http://127.0.0.1:{self.server.server_port}"
        if self.path.startswith("/q/requests/req/status"):
            return self._send({"status": "COMPLETED"})
        if self.path == "/q/requests/req":
            return self._send({"images": [{"url": base + "/files/out.png", "width": 8}], "seed": 1})
        if self.path.startswith("/files/"):
            data = b"\x89PNG fake"
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._send({"error": "not found"}, 404)


class Fal(unittest.TestCase):
    def setUp(self):
        self.srv = HTTPServer(("127.0.0.1", 0), _FakeFal)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{self.srv.server_port}"
        self._old = (fal.QUEUE_BASE, fal.REST_BASE, os.environ.get("FAL_KEY"))
        fal.QUEUE_BASE, fal.REST_BASE = base, base
        os.environ["FAL_KEY"] = "test-key-not-real"
        _FakeFal.calls = []

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        fal.QUEUE_BASE, fal.REST_BASE = self._old[0], self._old[1]
        if self._old[2] is None:
            os.environ.pop("FAL_KEY", None)
        else:
            os.environ["FAL_KEY"] = self._old[2]

    def test_requires_confirm(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(fal.FalError):
                fal.run("fal-ai/nano-banana-pro", {"prompt": "x"}, out_dir=d, project_dir=d, confirm=False)
            self.assertEqual(_FakeFal.calls, [])

    def test_run_uploads_local_files_downloads_outputs_and_counts_budget(self):
        with tempfile.TemporaryDirectory() as d:
            project.init_project(d, "t", max_calls=1)
            ref = os.path.join(d, "assets", "ref.png")
            with open(ref, "wb") as fh:
                fh.write(b"\x89PNG ref")
            res = fal.run(
                "fal-ai/nano-banana-pro/edit",
                {"prompt": "x", "image_urls": ["assets/ref.png"]},
                out_dir=os.path.join(d, "gen"),
                project_dir=d,
                confirm=True,
                base_dir=d,
            )
            self.assertEqual(len(res["files"]), 1)
            self.assertTrue(os.path.exists(res["files"][0]))
            submit = [c for c in _FakeFal.calls if c[0] == "POST" and c[1].startswith("/fal-ai/")][0]
            self.assertEqual(submit[2], "Key test-key-not-real")
            self.assertIn(b"/files/x.png", submit[3])  # local file replaced by uploaded URL
            put = [c for c in _FakeFal.calls if c[0] == "PUT"][0]
            self.assertIsNone(put[2])  # signed upload URL gets no fal key
            self.assertEqual(fal.budget(d)[0], 1)
            with self.assertRaises(fal.FalError):
                fal.run("fal-ai/nano-banana-pro", {"prompt": "y"}, out_dir=d, project_dir=d, confirm=True)

    def test_missing_local_file_is_an_error_not_a_paid_call(self):
        with tempfile.TemporaryDirectory() as d:
            project.init_project(d, "t")
            with self.assertRaises(fal.FalError):
                fal.run("fal-ai/x/edit", {"image_url": "assets/missing.png"}, out_dir=d, project_dir=d, confirm=True, base_dir=d)
            self.assertFalse([c for c in _FakeFal.calls if c[1].startswith("/fal-ai/")])

    def test_plan_prices_and_budget(self):
        with tempfile.TemporaryDirectory() as d:
            project.init_project(d, "t", max_calls=2)
            md, summary = fal.plan_table({"items": [
                {"endpoint": "fal-ai/nano-banana-pro", "purpose": "still", "count": 1, "unit": "image", "unit_price": 0.15},
                {"endpoint": "bytedance/seedance-2.0/image-to-video", "purpose": "motion", "count": 1, "unit": "second", "quantity": 5, "unit_price": 0.3024},
            ]}, d)
            self.assertAlmostEqual(summary["total"], 0.15 + 5 * 0.3024, places=4)
            self.assertFalse(summary["over_budget"])
            self.assertIn("1.66", md)
            _, s2 = fal.plan_table({"items": [{"endpoint": "a/b", "count": 3}]}, d)
            self.assertTrue(s2["over_budget"])
            self.assertEqual(s2["missing_prices"], ["a/b"])
            self.assertEqual(_FakeFal.calls, [])  # planning never calls fal

    def test_rejects_bad_endpoint(self):
        with self.assertRaises(fal.FalError):
            fal.submit("https://evil.example/x", {})


class Build(unittest.TestCase):
    SCRIBE = {"words": [
        {"text": "Kopi", "start": 0.2, "end": 0.5, "type": "word"}, {"text": " ", "start": 0.5, "end": 0.55, "type": "spacing"},
        {"text": "saya", "start": 0.55, "end": 0.9, "type": "word"}, {"text": "pahit.", "start": 0.95, "end": 1.4, "type": "word"},
        {"text": "Turunkan", "start": 2.2, "end": 2.8, "type": "word"}, {"text": "ke", "start": 2.85, "end": 2.95, "type": "word"},
        {"text": "92", "start": 3.0, "end": 3.4, "type": "word"}, {"text": "derajat.", "start": 3.45, "end": 4.0, "type": "word"},
    ]}

    def test_extract_formats(self):
        from slopguard import build
        self.assertEqual(len(build.extract_words(self.SCRIBE)), 7)  # spacing dropped
        whisper = {"segments": [{"words": [{"word": "a", "start": 0, "end": 0.2}, {"word": "b", "start": 0.3, "end": 0.5}]}]}
        self.assertEqual([w[0] for w in build.extract_words(whisper)], ["a", "b"])
        chunks = {"chunks": [{"text": "satu dua", "timestamp": [0.0, 1.0]}]}
        self.assertEqual(len(build.extract_words(chunks)), 2)

    def test_captions_break_on_sentences_and_keep_numbers(self):
        from slopguard import build
        cues = build.captions_from_words(build.extract_words(self.SCRIBE), lang="id")
        texts = [" ".join(c[2]) for c in cues]
        self.assertEqual(texts, ["Kopi saya pahit.", "Turunkan ke 92 derajat."])
        for (s, e, _), nxt in zip(cues, cues[1:] + [None]):
            self.assertGreaterEqual(e - s, 0.8 - 1e-6)
            if nxt:
                self.assertLessEqual(e, nxt[0])
        srt = build.to_srt(cues)
        self.assertEqual(captions.check_captions(srt).exit_code(), EXIT_CLEAN)

    def test_vertical_projects_get_short_caption_lines(self):
        from slopguard import cli
        long = {"words": [{"text": w, "start": i * 0.4, "end": i * 0.4 + 0.35, "type": "word"}
                          for i, w in enumerate("Air mendidih seratus derajat mengekstrak terlalu banyak senyawa pahit.".split())]}
        with tempfile.TemporaryDirectory() as d:
            project.init_project(d, "t", fmt="vertical")
            words = os.path.join(d, "words.json")
            with open(words, "w") as fh:
                json.dump(long, fh)
            out = os.path.join(d, "edit", "master.srt")
            cli.main(["captions", words, "--out", out])
            lines = [l for l in open(out).read().splitlines() if l and "-->" not in l and not l.isdigit()]
            self.assertTrue(lines and max(len(l) for l in lines) <= 28, lines)

    def test_balanced_split_has_no_orphans_and_keeps_numbers(self):
        from slopguard import build
        words, t = [], 0.2
        for w in "Air mendidih seratus derajat mengekstrak terlalu banyak senyawa pahit dari bubuk kopi.".split():
            words.append((w, t, t + 0.35))
            t += 0.42
        cues = build.captions_from_words(words, lang="id", max_chars=28)
        word_counts = [len(" ".join(c[2]).split()) for c in cues]
        self.assertGreaterEqual(min(word_counts), 3, cues)
        lines = [line for c in cues for line in c[2]]
        self.assertFalse(any(line.endswith("seratus") for line in lines), lines)
        for (s1, e1, _), (s2, _, _) in zip(cues, cues[1:]):
            self.assertGreaterEqual(round(s2 - e1, 3), round(2 / 30, 3))

    def test_edl_mapping(self):
        from slopguard import build
        words = build.extract_words(self.SCRIBE)
        out = build.map_to_output(words, [{"start": 2.0, "end": 4.2}])
        self.assertEqual(out[0][0], "Turunkan")
        self.assertAlmostEqual(out[0][1], 0.2, places=3)

    @unittest.skipUnless(helpers.have_ffmpeg(), "ffmpeg not installed")
    def test_master_hits_target(self):
        from slopguard import build
        with tempfile.TemporaryDirectory() as d:
            src = helpers.make_sloppy(os.path.join(d, "loud.mp4"))
            res = build.master_loudness(src, os.path.join(d, "out.mp4"))
            self.assertAlmostEqual(res["after_lufs"], -14.0, delta=1.0)
            self.assertLessEqual(res["after_true_peak"], -1.0)


if __name__ == "__main__":
    unittest.main()
