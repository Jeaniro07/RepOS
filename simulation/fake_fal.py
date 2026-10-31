#!/usr/bin/env python3
"""A local stand-in for fal.ai, speaking the same queue + storage protocol that
toolkit/slopguard/fal.py uses, and returning real media made with ffmpeg:

  image endpoints        -> PNG still        {"images": [{"url": ...}]}
  image/text-to-video    -> MP4 clip         {"video": {"url": ...}}
  text-to-speech         -> WAV narration    {"audio": {"url": ...}}   (ffmpeg flite voice)
  speech-to-text         -> word timings     {"text": ..., "words": [{"text","start","end","type"}]}

Speech-to-text returns the exact word timings recorded when the fake TTS made
the audio, so captions and cuts can be checked against known truth.
Every request is logged (method, path, endpoint, whether an Authorization
header was present) to --log; key values are never logged.

Usage: python3 fake_fal.py --port 0 --dir /tmp/fakefal --log calls.jsonl
Prints "READY <port>" when listening. Requires an ffmpeg with the flite filter
for speech (falls back to a tone when flite is missing).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
import uuid
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

FFMPEG = os.environ.get("FAKE_FAL_FFMPEG") or shutil.which("ffmpeg")
FONT = next((f for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") if os.path.exists(f)), None)
LOCK = threading.Lock()
STATE = {"requests": {}, "uploads": {}, "word_timings": {}}


def ff(*args):
    subprocess.run([FFMPEG, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *args], check=True, stdin=subprocess.DEVNULL)


def has_flite() -> bool:
    out = subprocess.run([FFMPEG, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return " flite " in out


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


class Media:
    def __init__(self, root: str):
        self.root = root
        os.makedirs(root, exist_ok=True)

    def path(self, name: str) -> str:
        return os.path.join(self.root, name)

    def image(self, prompt: str, size=(1080, 1920)) -> str:
        name = f"img-{uuid.uuid4().hex[:8]}.png"
        hue = int(hashlib.md5(prompt.encode()).hexdigest()[:2], 16) * 360 // 255
        label = esc("fake fal image: " + prompt[:40])
        vf = f"hue=h={hue}"
        if FONT:
            vf += f",drawtext=fontfile={FONT}:text='{label}':fontcolor=white:fontsize=34:x=(w-tw)/2:y=h*0.9"
        ff("-f", "lavfi", "-i", f"mandelbrot=s={size[0]}x{size[1]}:rate=1", "-frames:v", "1", "-vf", vf, self.path(name))
        return name

    def clip_from_image(self, image_path: str, duration: float, size=(1080, 1920)) -> str:
        name = f"vid-{uuid.uuid4().hex[:8]}.mp4"
        frames = int(duration * 30)
        ff(
            "-loop", "1", "-i", image_path, "-t", f"{duration}",
            "-vf", f"scale={size[0] * 2}:{size[1] * 2},zoompan=z='1+0.25*on/{frames}':x='iw/2-(iw/zoom/2)+on*2':y='ih/2-(ih/zoom/2)':d={frames}:s={size[0]}x{size[1]}:fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", self.path(name),
        )
        return name

    def speech(self, text: str) -> tuple:
        """Synthesise word by word so every word's start/end is known exactly."""
        name = f"tts-{uuid.uuid4().hex[:8]}.wav"
        work = self.path(name + ".parts")
        os.makedirs(work, exist_ok=True)
        words, parts, t = [], [], 0.25
        flite = has_flite()
        silence = os.path.join(work, "gap.wav")
        ff("-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "0.25", "-c:a", "pcm_s16le", silence)
        parts.append(silence)
        for i, w in enumerate(text.split()):
            clean = w.strip(",.!?")
            p = os.path.join(work, f"w{i:04d}.wav")
            if flite:
                ff("-f", "lavfi", "-i", f"flite=text='{esc(clean)}':voice=slt", "-af", "aresample=48000,silenceremove=start_periods=1:start_threshold=-50dB:stop_periods=1:stop_threshold=-50dB", "-ac", "1", "-c:a", "pcm_s16le", p)
            else:
                ff("-f", "lavfi", "-i", f"sine=f={180 + (i % 5) * 40}:d={0.08 * len(clean) + 0.1}", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", p)
            with wave.open(p) as wf:
                dur = wf.getnframes() / wf.getframerate()
            words.append({"text": w, "start": round(t, 3), "end": round(t + dur, 3), "type": "word"})
            parts.append(p)
            gap = 0.55 if w.endswith((".", "!", "?")) else (0.25 if w.endswith(",") else 0.07)
            g = os.path.join(work, f"g{i:04d}.wav")
            ff("-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{gap}", "-c:a", "pcm_s16le", g)
            parts.append(g)
            t += dur + gap
        lst = os.path.join(work, "list.txt")
        with open(lst, "w") as fh:
            fh.writelines(f"file '{p}'\n" for p in parts)
        ff("-f", "concat", "-safe", "0", "-i", lst, "-c:a", "pcm_s16le", self.path(name))
        shutil.rmtree(work, ignore_errors=True)
        return name, words


def _digest(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run_model(endpoint: str, payload: dict, media: Media, base: str) -> dict:
    e = endpoint.lower()
    if "speech-to-text" in e or "scribe" in e or "wizper" in e or "whisper" in e:
        url = payload.get("audio_url", "")
        local = media.path(os.path.basename(urlparse(url).path))
        # Match by content, so an uploaded copy of our own TTS output is recognised.
        words = STATE["word_timings"].get(_digest(local)) if os.path.exists(local) else None
        if words is None:
            return {"text": "", "words": [], "note": "fake server only transcribes audio made by its own TTS"}
        return {"text": " ".join(w["text"] for w in words), "language_code": "ind", "words": words}
    if "tts" in e or "speech-2" in e or "text-to-speech" in e:
        name, words = media.speech(payload.get("text") or payload.get("prompt") or "")
        STATE["word_timings"][_digest(media.path(name))] = words
        return {"audio": {"url": f"{base}/files/{name}", "content_type": "audio/wav"}}
    if "video" in e or "seedance" in e or "kling" in e or "veo" in e:
        src = payload.get("image_url", "")
        local = media.path(os.path.basename(urlparse(src).path)) if src.startswith(base) else None
        if not local or not os.path.exists(local):
            local = media.path(media.image(payload.get("prompt", "video")))
        dur = float(str(payload.get("duration", "4")).rstrip("s") or 4)
        name = media.clip_from_image(local, dur)
        return {"video": {"url": f"{base}/files/{name}", "content_type": "video/mp4"}}
    name = media.image(payload.get("prompt", "image"))
    return {"images": [{"url": f"{base}/files/{name}", "content_type": "image/png", "width": 1080, "height": 1920}], "seed": 42}


def make_handler(media: Media, log_path: str):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _log(self, **extra):
            entry = {"t": round(time.time(), 3), "method": self.command, "path": self.path.split("?")[0],
                     "auth_header": bool(self.headers.get("Authorization")), **extra}
            with LOCK, open(log_path, "a") as fh:
                fh.write(json.dumps(entry) + "\n")

        def _json(self, obj, code=200):
            data = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _authorized(self) -> bool:
            return (self.headers.get("Authorization") or "").startswith("Key ") and len(self.headers["Authorization"]) > 8

        @property
        def base(self):
            return f"http://127.0.0.1:{self.server.server_port}"

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            path = self.path.split("?")[0]
            if not self._authorized():
                self._log(status=401)
                return self._json({"detail": "Missing or invalid Authorization: Key <FAL_KEY>"}, 401)
            if path == "/storage/upload/initiate":
                req = json.loads(body or b"{}")
                name = f"up-{uuid.uuid4().hex[:8]}-{os.path.basename(req.get('file_name', 'upload.bin'))}"
                STATE["uploads"][name] = True
                self._log(status=200, kind="upload-initiate")
                return self._json({"upload_url": f"{self.base}/put/{name}", "file_url": f"{self.base}/files/{name}"})
            endpoint = path.strip("/")
            payload = json.loads(body or b"{}")
            rid = uuid.uuid4().hex
            owner_alias = "/".join(endpoint.split("/")[:2])
            STATE["requests"][rid] = {"endpoint": endpoint, "payload": payload, "status": "IN_QUEUE", "polls": 0}
            self._log(status=200, kind="submit", endpoint=endpoint, request_id=rid)
            q = f"{self.base}/{owner_alias}/requests/{rid}"
            return self._json({"request_id": rid, "status_url": q + "/status", "response_url": q, "cancel_url": q + "/cancel"})

        def do_PUT(self):
            data = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            name = self.path.split("/put/", 1)[-1]
            with open(media.path(name), "wb") as fh:
                fh.write(data)
            self._log(status=200, kind="upload-put", bytes=len(data))
            return self._json({})

        def do_GET(self):
            path = self.path.split("?")[0]
            if path.startswith("/files/"):
                p = media.path(os.path.basename(path))
                if not os.path.exists(p):
                    return self._json({"detail": "not found"}, 404)
                data = open(p, "rb").read()
                self._log(status=200, kind="cdn-download", bytes=len(data))
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if not self._authorized():
                self._log(status=401)
                return self._json({"detail": "unauthorized"}, 401)
            parts = path.strip("/").split("/")
            if "requests" in parts:
                rid = parts[parts.index("requests") + 1]
                req = STATE["requests"].get(rid)
                if not req:
                    return self._json({"detail": "unknown request"}, 404)
                if path.endswith("/status"):
                    req["polls"] += 1
                    if req["status"] != "COMPLETED" and req["polls"] >= 2:
                        try:
                            req["result"] = run_model(req["endpoint"], req["payload"], media, self.base)
                        except Exception as exc:  # report like fal: COMPLETED with an error
                            req["error"] = str(exc)
                        req["status"] = "COMPLETED"
                    elif req["status"] == "IN_QUEUE":
                        req["status"] = "IN_PROGRESS"
                    self._log(status=200, kind="status", state=req["status"])
                    out = {"status": req["status"], "logs": []}
                    if req.get("error"):
                        out["error"] = req["error"]
                    return self._json(out)
                self._log(status=200, kind="result", endpoint=req["endpoint"])
                return self._json(req.get("result", {}))
            return self._json({"detail": "not found"}, 404)

    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(Media(a.dir), a.log))
    print(f"READY {srv.server_port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
