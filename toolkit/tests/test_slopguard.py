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

    def test_rejects_bad_endpoint(self):
        with self.assertRaises(fal.FalError):
            fal.submit("https://evil.example/x", {})


if __name__ == "__main__":
    unittest.main()
