#!/usr/bin/env python3
"""End-to-end simulation: a Rakazo bot using the antislop-video plugin.

What is real and what is simulated
  REAL   Rakazo's own plugin parser (parsePluginDirectory from elie222/rakazo) on rakazo-plugin/
  REAL   the toolkit is cloned from GitHub (this repo, --ref) exactly as the setup skill says,
         setup.sh downloads a static ffmpeg, every slopguard command runs for real,
         every ffmpeg render runs for real and produces a real MP4
  SIM    the bot computer: a fresh non-root user, empty home, Python 3.11, PATH without
         ffmpeg/ffprobe/node/apt/pip/uv (like Rakazo's Debian computer image)
  SIM    fal.ai: simulation/fake_fal.py speaks fal's queue + storage protocol and returns
         media made locally (flite voice, still, zoom clip, exact word timings)
  SIM    the user's footage: animated placeholder clips labelled "simulasi"
  SIM    the agent's writing: brief, spec, scripts and plan come from simulation/scenario/
  NOT    the LLM itself and the slop-critic run (needs Rakazo + a model); their inputs are checked

Usage (root recommended, to create the isolated user):
  python3 simulation/run_simulation.py --ref <branch> [--rakazo-src /path/to/rakazo] [--out simulation/output]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import pwd
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(ROOT, "simulation")
SCEN = os.path.join(SIM, "scenario")
FAKE_KEY = "sim-NOT-A-REAL-FAL-KEY-7f3a9c"
BLOCKED_TOOLS = {"ffmpeg", "ffprobe", "ffplay", "node", "nodejs", "npm", "npx", "apt", "apt-get", "dpkg", "pip", "pip3",
                 "uv", "uvx", "docker", "sudo", "su", "python3", "python", "pytest", "brew", "snap", "yarn", "pnpm", "bun"}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
USER = "rakazo-sim"


class Sim:
    def __init__(self, args):
        self.args = args
        self.steps = []
        self.work = tempfile.mkdtemp(prefix="antislop-sim-", dir="/tmp")  # a non-root user must traverse it
        os.chmod(self.work, 0o755)
        self.home = os.path.join(self.work, "home")
        self.sysbin = os.path.join(self.work, "sysbin")
        self.env = {}
        self.as_user = os.geteuid() == 0
        self.fake = None
        self.fake_log = os.path.join(self.work, "fake-fal-calls.jsonl")
        self.project = None

    # ------------------------------------------------------------ environment

    def make_computer(self):
        os.makedirs(self.sysbin)
        for d in ("/usr/local/bin", "/usr/bin", "/bin"):
            for name in sorted(os.listdir(d)):
                src, dst = os.path.join(d, name), os.path.join(self.sysbin, name)
                if name in BLOCKED_TOOLS or os.path.exists(dst) or not os.access(src, os.X_OK) or os.path.isdir(src):
                    continue
                if name.startswith(("python3.", "ffmpeg", "node")) and name != "python3.11":
                    continue
                os.symlink(src, dst)
        py = shutil.which("python3.11") or "/usr/bin/python3.11"
        os.symlink(py, os.path.join(self.sysbin, "python3"))
        os.symlink(py, os.path.join(self.sysbin, "python"))
        if self.as_user:
            try:
                pwd.getpwnam(USER)
            except KeyError:
                subprocess.run(["useradd", "-u", "1500", "-M", "-s", "/bin/bash", USER], check=True)
            os.makedirs(self.home)
            shutil.chown(self.home, USER, USER)
        else:
            os.makedirs(self.home)
        ca_src = os.environ.get("SSL_CERT_FILE") or os.environ.get("GIT_SSL_CAINFO")
        ca = None
        if ca_src and os.path.exists(ca_src):
            ca = os.path.join(self.work, "ca.crt")
            shutil.copy(ca_src, ca)
            os.chmod(ca, 0o644)
        no_proxy = (os.environ.get("NO_PROXY", "") + ",127.0.0.1,localhost").strip(",")
        self.env = {
            "HOME": self.home, "USER": USER, "LANG": "C.UTF-8", "TERM": "dumb",
            "PATH": f"{self.home}/.local/bin:{self.sysbin}",
            "GIT_TERMINAL_PROMPT": "0", "NO_PROXY": no_proxy, "no_proxy": no_proxy,
        }
        for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
            if os.environ.get(k):
                self.env[k] = os.environ[k]
        if ca:
            for k in ("SSL_CERT_FILE", "GIT_SSL_CAINFO", "CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE"):
                self.env[k] = ca

    def sh(self, step, skill, cmd, expect=0, timeout=1200, show=True, actor="bot"):
        """Run a command on the simulated bot computer and record it."""
        env_args = [f"{k}={v}" for k, v in self.env.items()]
        full = ["env", "-i", *env_args, "bash", "-c", f"set -o pipefail; cd ~ && {cmd}"]
        if self.as_user:
            full = ["runuser", "-u", USER, "--", *full]
        t0 = time.time()
        p = subprocess.run(full, capture_output=True, text=True, errors="replace", timeout=timeout)
        out = (p.stdout + ("\n" + p.stderr if p.stderr.strip() else "")).replace(FAKE_KEY, "***")
        ok = expect is None or p.returncode == expect
        self.steps.append({"step": step, "skill": skill, "actor": actor, "command": cmd, "exit": p.returncode,
                           "expected": expect, "ok": ok, "seconds": round(time.time() - t0, 1), "output": out[-3000:]})
        mark = "OK " if ok else "FAIL"
        print(f"[{mark}] {step} (exit {p.returncode}, {time.time() - t0:.1f}s)")
        if show and not ok:
            print(textwrap.indent(out[-2500:], "      "))
        return p.returncode, out

    def note(self, step, skill, text, actor="user"):
        self.steps.append({"step": step, "skill": skill, "actor": actor, "command": None, "exit": None,
                           "expected": None, "ok": True, "seconds": 0, "output": text})
        print(f"[ .. ] {step}")

    def write(self, rel, content, mode=0o644):
        """The agent writes a file on its computer."""
        path = os.path.join(self.home, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        if self.as_user:
            cur = os.path.dirname(path)
            while cur.startswith(self.home) and cur != self.home:
                shutil.chown(cur, USER, USER)
                cur = os.path.dirname(cur)
            shutil.chown(path, USER, USER)
        return path

    def read(self, rel):
        with open(os.path.join(self.home, rel), encoding="utf-8") as fh:
            return fh.read()

    # ------------------------------------------------------------ fake fal

    def start_fake_fal(self):
        d = os.path.join(self.work, "fakefal")
        self.fake = subprocess.Popen(
            [sys.executable, os.path.join(SIM, "fake_fal.py"), "--port", "0", "--dir", d, "--log", self.fake_log],
            stdout=subprocess.PIPE, text=True,
        )
        line = self.fake.stdout.readline().strip()
        port = int(line.split()[1])
        base = f"http://127.0.0.1:{port}"
        self.env["FAL_QUEUE_BASE"] = base
        self.env["FAL_REST_BASE"] = base
        return base

    def stop(self):
        if self.fake:
            self.fake.send_signal(signal.SIGTERM)

    def fake_calls(self):
        if not os.path.exists(self.fake_log):
            return []
        return [json.loads(x) for x in open(self.fake_log)]


# ---------------------------------------------------------------- the run


def rakazo_preview(sim: Sim):
    src = sim.args.rakazo_src
    if not src or not os.path.exists(src):
        src = os.path.join(sim.work, "rakazo")
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse", "https://github.com/elie222/rakazo", src], check=True)
        subprocess.run(["git", "-C", src, "sparse-checkout", "set", "packages/adapters/src", "packages/core/src"], check=True)
    harness = os.path.join(SIM, "rakazo-preview")
    p = subprocess.run(
        ["node", "--experimental-strip-types", "--no-warnings", "--import", "./register.mjs", "preview.mjs", os.path.join(ROOT, "rakazo-plugin")],
        cwd=harness, env=dict(os.environ, RAKAZO_SRC=src), capture_output=True, text=True,
    )
    sha = subprocess.run(["git", "-C", src, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    sim.steps.append({"step": f"Rakazo Preview: parsePluginDirectory (elie222/rakazo@{sha})", "skill": "Integrations → From GitHub", "actor": "rakazo",
                      "command": "node … preview.mjs rakazo-plugin", "exit": p.returncode, "expected": 0, "ok": p.returncode == 0,
                      "seconds": 0, "output": p.stdout[-3000:] + p.stderr[-1000:]})
    print(f"[{'OK ' if p.returncode == 0 else 'FAIL'}] Rakazo Preview")
    v = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "validate_plugin.py"), os.path.join(ROOT, "rakazo-plugin")], capture_output=True, text=True)
    sim.steps.append({"step": "validate_plugin.py (batas ukuran & format)", "skill": "-", "actor": "rakazo", "command": "python3 scripts/validate_plugin.py rakazo-plugin",
                      "exit": v.returncode, "expected": 0, "ok": v.returncode == 0, "seconds": 0, "output": v.stdout})
    return json.loads(p.stdout) if p.returncode == 0 else {}


def setup_block():
    text = open(os.path.join(ROOT, "rakazo-plugin", "skills", "video-toolkit-setup", "SKILL.md"), encoding="utf-8").read()
    return re.search(r"## Install or update\s+```bash\n(.*?)```", text, re.S).group(1).strip()


def shot_script(n, dur, kind, src=None, start=0.0, version=2):
    """Agent-written ffmpeg command for one shot (1080x1920@30, identical encode settings for -c copy concat)."""
    enc = "-an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 30"
    out = f"edit/clips/shot{n}.mp4"
    if kind == "footage":
        return (f"ffmpeg -hide_banner -loglevel error -y -ss {start:.3f} -i {src} -t {dur:.3f} "
                f"-vf \"scale=1080:1920,setsar=1,fps=30\" {enc} {out}")
    if kind == "diagram":
        base = (f"color=c=0x1d1a17:s=1080x1920:r=30:d={dur:.3f}[bg];"
                f"[bg]drawtext=fontfile={FONT}:textfile=edit/text/temp.txt:fontcolor=0xe0703a:fontsize=150:x=(w-tw)/2:y=560")
        if version == 1:  # first draft: a static title card (a default the QA should catch)
            vf = base + f",drawtext=fontfile={FONT}:textfile=edit/text/label.txt:fontcolor=0xf4efe6:fontsize=56:x=(w-tw)/2:y=820[v]"
            return f"ffmpeg -hide_banner -loglevel error -y -f lavfi -i nullsrc=s=16x16:d=0.1 -filter_complex \"{vf}\" -map \"[v]\" -t {dur:.3f} {enc} {out}"
        vf = (base + f",drawtext=fontfile={FONT}:textfile=edit/text/label.txt:fontcolor=0xf4efe6:fontsize=56:x=(w-tw)/2:y=820:enable='gte(t,0.5)'[t];"
              f"color=c=0xe0703a:s=900x70:r=30:d={dur:.3f}[bar];"
              f"[t][bar]overlay=x='90-900+900*min(1,max(0,(t-0.5)/2.6))':y=980:shortest=1,"
              f"drawtext=fontfile={FONT}:textfile=edit/text/bar.txt:fontcolor=0x1d1a17:fontsize=44:x=120:y=992:enable='gte(t,3.1)'[v]")
        return f"ffmpeg -hide_banner -loglevel error -y -f lavfi -i nullsrc=s=16x16:d=0.1 -filter_complex \"{vf}\" -map \"[v]\" -t {dur:.3f} {enc} {out}"
    if kind == "generated":
        vf = (f"scale=1080:1920,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=2,"
              f"drawtext=fontfile={FONT}:textfile=edit/text/temp92.txt:fontcolor=white:fontsize=150:borderw=6:bordercolor=0x1d1a17:x=(w-tw)/2:y=520:enable='gte(t,0.4)'")
        return f"ffmpeg -hide_banner -loglevel error -y -i {src} -t {dur:.3f} -vf \"{vf}\" {enc} {out}"
    raise ValueError(kind)


def run(sim: Sim):
    a = sim.args
    preview = rakazo_preview(sim)
    skills = [s["name"] for s in preview.get("skills", [])]

    sim.make_computer()
    base = sim.start_fake_fal()
    sim.note("Komputer bot siap: user non-root, Python 3.11, tanpa ffmpeg/node/apt/pip/uv di PATH", "-", "", actor="sim")
    sim.sh("Cek awal: ffmpeg memang tidak ada", "-", "command -v ffmpeg || echo 'ffmpeg: tidak ada'; python3 --version; id -u", expect=0)

    # 1. Toolkit setup, verbatim from the skill
    sim.env["ANTISLOP_REF"] = a.ref
    sim.sh("video-toolkit-setup: clone repo dari GitHub + setup.sh + doctor", "video-toolkit-setup", setup_block(), expect=0)
    sim.sh("ffmpeg kini bisa dipanggil langsung (untuk video-assembly)", "video-toolkit-setup", "command -v ffmpeg ffprobe slopguard && ffmpeg -version | head -1", expect=0)
    sim.sh("Tes toolkit di komputer bot", "video-toolkit-setup", "cd ~/antislop/RepOS/toolkit && python3 -m unittest discover -s tests 2>&1 | tail -3", expect=0)

    # 2. Secret
    sim.note("request_secret {name: fal-key, auth: command} → pengguna menyimpan kunci di kartu terlindung", "fal-media", "", actor="user")
    sim.env["FAL_KEY"] = FAKE_KEY
    sim.sh("doctor melihat $FAL_KEY tanpa menampilkannya", "video-toolkit-setup", "slopguard doctor | grep FAL_KEY", expect=0)

    # 3. /video
    proj = "videos/kopi-pahit"
    sim.project = proj
    sim.note("/video 20 detik vertikal: kenapa kopi saya pahit padahal bijinya mahal", "video (command)", "", actor="user")
    sim.sh("slopguard init proyek", "antislop-video-director", f"slopguard init ~/{proj} --title 'Kenapa kopi saya pahit' --format vertical --duration 20 --lang id --max-calls 4", expect=0)
    sim.write(f"{proj}/BRIEF.md", open(os.path.join(SCEN, "BRIEF.md")).read())
    sim.write(f"{proj}/SPEC.md", open(os.path.join(SCEN, "SPEC.md")).read())
    sim.note("Brief diisi, 3 alur cerita diusulkan, pengguna memilih alur 1; SPEC.md ditulis", "antislop-video-director", "", actor="bot")

    # 4. Script loop
    sim.write(f"{proj}/script.md", open(os.path.join(SCEN, "script-v1.md")).read())
    sim.sh("Naskah draf 1 → lint (harus DIBLOKIR)", "antislop-script", f"cd ~/{proj} && slopguard lint-script script.md | sed -n 3,6p", expect=1)
    sim.sh("/cek-slop pada draf 1 (ringkas)", "cek-slop (command)", f"cd ~/{proj} && slopguard lint-script script.md --json | python3 -c \"import json,sys;d=json.load(sys.stdin);print(d['counts']);print(sorted({{f['gate'] for f in d['findings']}}))\"", expect=1)
    sim.write(f"{proj}/script.md", open(os.path.join(SCEN, "script-v2.md")).read())
    sim.sh("Naskah draf 2 → lint (harus CLEAR)", "antislop-script", f"cd ~/{proj} && slopguard lint-script script.md | sed -n 3,6p", expect=0)

    # 5. Ledger (estimated times) + plan
    est = ("shot,start,end,narration,idea,visual,source_type,source,license,real_person,notes\n"
           "1,0,4.5,Kopi saya selalu pahit,masalahnya terlihat,kopi dituang,footage,assets/pour.mp4,rekaman sendiri,no,\n"
           "2,4.5,6.5,Ternyata masalahnya air,penyebab: air,ketel mendidih,footage,assets/kettle.mp4,rekaman sendiri,no,\n"
           "3,6.5,12,Air mendidih 100 derajat,ekstraksi berlebih,diagram suhu + batang senyawa pahit,code,data dari [1],,no,\n"
           "4,12,16.5,turunkan ke 92 derajat,solusi,uap di atas cangkir + angka 92,generated,fal (rencana),,no,\n"
           "5,16.5,20,Hasilnya lebih manis,hasil,mencicipi,footage,assets/taste.mp4,rekaman sendiri,no,\n")
    sim.write(f"{proj}/ledger.csv", est)
    sim.write(f"{proj}/GENERATION_PLAN.md", open(os.path.join(SCEN, "GENERATION_PLAN.md")).read())
    sim.sh("Ledger rencana → check-ledger", "antislop-video-director", f"cd ~/{proj} && slopguard check-ledger ledger.csv | sed -n 3,5p", expect=0)

    # 6. Money guard
    narr = open(os.path.join(SCEN, "narration-tts.txt")).read().strip()
    sim.write(f"{proj}/gen/voice.json", json.dumps({"text": narr}, ensure_ascii=False))
    sim.sh("fal run TANPA --confirm (harus ditolak, tanpa panggilan jaringan)", "fal-media", f"cd ~/{proj} && slopguard fal run fal-ai/elevenlabs/tts/eleven-v3 --input gen/voice.json --out gen/voice", expect=3)
    submits_before = sum(1 for c in sim.fake_calls() if c.get("kind") == "submit")
    sim.note("Pengguna: \u201cYa, setuju rencana 4 panggilan.\u201d", "fal-media", "", actor="user")

    # 7. Paid calls (fake fal)
    code, out = sim.sh("fal 1/4: TTS narasi", "fal-media", f"cd ~/{proj} && slopguard fal run fal-ai/elevenlabs/tts/eleven-v3 --input gen/voice.json --out gen/voice --label voice --confirm", expect=0)
    voice = json.loads(out[out.index("{"): out.rindex("}") + 1])["files"][0]
    voice_rel = os.path.relpath(voice, os.path.join(sim.home, proj))
    sim.write(f"{proj}/gen/stt.json", json.dumps({"audio_url": voice_rel}))
    code, out = sim.sh("fal 2/4: transkrip per kata (file lokal di-upload otomatis)", "fal-media", f"cd ~/{proj} && slopguard fal run fal-ai/elevenlabs/speech-to-text/scribe-v2 --input gen/stt.json --out gen/transcript --label stt --confirm", expect=0)
    transcript_json = glob.glob(os.path.join(sim.home, proj, "gen", "transcript", "stt-*.json"))[0]
    sim.write(f"{proj}/gen/still.json", json.dumps({"prompt": "steam rising from a ceramic coffee cup on a wooden table, morning side light, no people, no text", "aspect_ratio": "9:16"}))
    code, out = sim.sh("fal 3/4: still shot 4", "fal-media", f"cd ~/{proj} && slopguard fal run fal-ai/nano-banana-pro --input gen/still.json --out gen/shot4 --label shot4-still --confirm", expect=0)
    still = json.loads(out[out.index("{"): out.rindex("}") + 1])["files"][0]
    sim.write(f"{proj}/gen/motion.json", json.dumps({"prompt": "slow steam drift, locked camera", "image_url": os.path.relpath(still, os.path.join(sim.home, proj)), "duration": "5"}))
    code, out = sim.sh("fal 4/4: gerak dari still", "fal-media", f"cd ~/{proj} && slopguard fal run bytedance/seedance-2.0/image-to-video --input gen/motion.json --out gen/shot4 --label shot4-motion --confirm", expect=0)
    clip = [f for f in json.loads(out[out.index("{"): out.rindex("}") + 1])["files"] if f.endswith(".mp4")][0]
    sim.sh("Panggilan ke-5 di luar rencana (harus ditolak oleh batas anggaran)", "fal-media", f"cd ~/{proj} && slopguard fal run fal-ai/nano-banana-pro --arg prompt=extra --out gen/extra --confirm", expect=3)
    sim.sh("Lihat hasil generatif di contact sheet sebelum dipakai", "fal-media", f"cd ~/{proj} && slopguard sheet {clip} --out gen/shot4/sheet --count 6", expect=0)

    # 8. User footage arrives (simulated placeholders)
    for name, c0, c1, label in (("pour", "0x5b3a29", "0xc89b6d", "kopi dituang"), ("kettle", "0x2f3b44", "0x9fb4c0", "ketel mendidih"), ("taste", "0x6d4c3d", "0xe8c9a6", "mencicipi")):
        sim.write(f"{proj}/edit/text/{name}.txt", f"FOOTAGE PENGGUNA (simulasi): {label}")
        sim.sh(f"(simulasi) footage pengguna: assets/{name}.mp4", "-", (
            f"cd ~/{proj} && ffmpeg -hide_banner -loglevel error -y -f lavfi -i gradients=s=1080x1920:c0={c0}:c1={c1}:speed=0.06:d=12:r=30 "
            f"-vf \"drawtext=fontfile={FONT}:textfile=edit/text/{name}.txt:fontcolor=white:fontsize=34:x=40:y=170:box=1:boxcolor=black@0.5:boxborderw=12\" "
            f"-c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p assets/{name}.mp4"), expect=0, actor="sim")

    # 9. Assembly from the transcript (cuts at sentence gaps)
    words = json.load(open(transcript_json))["result"]["words"]
    sentences, cur = [], []
    for w in words:
        cur.append(w)
        if w["text"].endswith((".", "!", "?")):
            sentences.append(cur)
            cur = []
    if cur:
        sentences.append(cur)
    bounds = [0.0]
    for s_prev, s_next in zip(sentences, sentences[1:]):
        bounds.append(round((s_prev[-1]["end"] + s_next[0]["start"]) / 2, 3))
    total = round(sentences[-1][-1]["end"] + 0.8, 3)
    bounds.append(total)
    durs = [round(b - a_, 3) for a_, b in zip(bounds, bounds[1:])]
    if abs(total - 20) > 2:
        cfg = json.loads(sim.read(f"{proj}/slopguard.json"))
        cfg["duration"] = round(total)
        sim.write(f"{proj}/slopguard.json", json.dumps(cfg, indent=2) + "\n")
    sim.write(f"{proj}/edit/text/temp.txt", "100°C")
    sim.write(f"{proj}/edit/text/label.txt", "air mendidih")
    sim.write(f"{proj}/edit/text/bar.txt", "senyawa pahit ikut larut")
    sim.write(f"{proj}/edit/text/temp92.txt", "92°C")
    plan = [("footage", "assets/pour.mp4", 1.0), ("footage", "assets/kettle.mp4", 2.0), ("diagram", None, 0), ("generated", clip, 0), ("footage", "assets/taste.mp4", 3.0)]
    new_ledger = ["shot,start,end,narration,idea,visual,source_type,source,license,real_person,notes"]
    ideas = ["masalahnya terlihat", "penyebab: air", "ekstraksi berlebih", "solusi", "hasil"]
    visuals = ["kopi dituang", "ketel mendidih", "diagram suhu + batang senyawa pahit", "uap di atas cangkir + angka 92", "mencicipi"]
    rid = os.path.basename(clip).split("-")[2] if clip.count("-") >= 2 else "?"
    for i, ((kind, src, start), d) in enumerate(zip(plan, durs), start=1):
        st = {"footage": "footage", "diagram": "code", "generated": "generated"}[kind]
        source = {"footage": src, "diagram": "data dari [1]", "generated": f"fal-ai/nano-banana-pro + bytedance/seedance-2.0/image-to-video ({rid})"}[kind]
        lic = "rekaman sendiri" if kind == "footage" else ""
        text = " ".join(w["text"] for w in sentences[i - 1]).replace(",", "")
        new_ledger.append(f"{i},{bounds[i - 1]},{bounds[i]},{text},{ideas[i - 1]},{visuals[i - 1]},{st},{source},{lic},no,")
    sim.write(f"{proj}/ledger.csv", "\n".join(new_ledger) + "\n")
    sim.note(f"Potongan diambil dari jeda antar-kalimat di transkrip: {bounds}", "video-assembly", "", actor="bot")
    srt = "edit/master.srt"
    sim.sh("Caption dari timestamp kata (slopguard captions)", "video-assembly", f"cd ~/{proj} && slopguard captions {os.path.relpath(transcript_json, os.path.join(sim.home, proj))} --out {srt} --lang id", expect=0)

    def render(version):
        lines = ["set -e", "mkdir -p edit/clips"]
        for i, ((kind, src, start), d) in enumerate(zip(plan, durs), start=1):
            lines.append(shot_script(i, d, kind, src, start, version=version))
        lines.append("printf \"file 'clips/shot%d.mp4'\\n\" 1 2 3 4 5 > edit/clips.txt")
        lines.append("ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i edit/clips.txt -c copy edit/picture.mp4")
        style = "FontName=DejaVu Sans,Bold=1,FontSize=11,PrimaryColour=&H00FFFFFF,OutlineColour=&H00171A1D,BorderStyle=1,Outline=1.2,Shadow=0,Alignment=2,MarginV=58"
        lines.append(f"ffmpeg -hide_banner -loglevel error -y -i edit/picture.mp4 -i {voice_rel} "
                     f"-filter_complex \"[0:v]subtitles={srt}:fontsdir={FONT_DIR}:force_style='{style}'[v];[1:a]apad,atrim=0:{total}[a]\" "
                     f"-map \"[v]\" -map \"[a]\" -t {total} -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k edit/preview_raw.mp4")
        lines.append("slopguard master edit/preview_raw.mp4 --out edit/preview.mp4")
        sim.write(f"{proj}/edit/render_v{version}.sh", "\n".join(lines) + "\n")
        return sim.sh(f"Render v{version}: shot per segmen → concat -c copy → caption TERAKHIR → master -14 LUFS", "video-assembly", f"cd ~/{proj} && bash edit/render_v{version}.sh", expect=0)

    render(1)
    code, out = sim.sh("QA pass 1 (harus menemukan kartu judul diam di shot 3)", "video-qa", f"cd ~/{proj} && slopguard qa edit/preview.mp4 --captions {srt} --json > edit/qa1.json; ec=$?; python3 -c \"import json;d=json.load(open('edit/qa1.json'));print(d['verdict']);[print(f['tier'],f['gate'],f.get('at'),f['message']) for f in d['findings']]\"; exit $ec", expect=2)
    sim.note("Perbaikan: shot 3 diubah dari kartu diam menjadi diagram yang bergerak sesuai narasi (batang 'senyawa pahit' terisi)", "video-qa", "", actor="bot")
    render(2)
    code, out = sim.sh("QA pass 2", "video-qa", f"cd ~/{proj} && slopguard qa edit/preview.mp4 --captions {srt}", expect=0)

    # 10. Critic inputs, review, delivery
    critic = ["BRIEF.md", "SPEC.md", "script.md", "ledger.csv", "edit/qa/qa-report.md", "edit/qa/overview.jpg", "edit/qa/cuts.jpg"]
    sim.sh("Bahan untuk helper slop-critic tersedia (run_subagent dijalankan oleh Rakazo)", "video-qa", f"cd ~/{proj} && ls -la " + " ".join(critic), expect=0)
    qa = json.loads(subprocess.run(["cat", os.path.join(sim.home, proj, "edit", "qa", "qa-report.json")], capture_output=True, text=True).stdout)
    m = qa["metrics"]
    review = textwrap.dedent(f"""\
        # REVIEW: Kenapa kopi saya pahit

        - Verdict QA: {qa['verdict']}
        - Diukur: {m.get('size')} @ {m.get('fps')} fps, {m.get('duration (s)')} s, {m.get('integrated loudness (LUFS)')} LUFS, true peak {m.get('true peak (dBTP)')} dBTP,
          {m.get('cuts detected')} potongan, gambar beku {m.get('frozen share of runtime')}, caption {m.get('captions: mean reading speed (chars/s)')} karakter/detik.
        - Dilihat: overview.jpg dan cuts.jpg. Tidak didengar: saya tidak bisa mendengar; mix hanya diukur.
        - Keputusan kreatif: alur 1 (masalah → penyebab → angka → hasil); alur 2 dan 3 tidak dibuat.
        - Perbaikan dari QA pass 1: kartu judul diam di shot 3 diganti diagram bergerak.
        - Shot terlemah: shot 4 (generatif); dengan waktu lebih, ganti dengan footage uap asli dari pengguna.
        - Generatif: shot 4 saja ({m.get('ledger: runtime by source')}). Rekomendasi: label AI tidak wajib untuk uap kopi non-realistis, tetapi aman dinyalakan.
        - Waiver: tidak ada.
        - Sumber: [1] Specialty Coffee Association, Water Quality Handbook.
        """)
    sim.write(f"{proj}/REVIEW.md", review)
    sim.sh("Serahkan: final.mp4 + SRT + REVIEW + ledger (tanpa mengunggah)", "antislop-video-director",
           f"cd ~/{proj} && mkdir -p deliver && cp edit/preview.mp4 deliver/final.mp4 && cp {srt} deliver/final.srt && cp REVIEW.md ledger.csv deliver/ && "
           "printf '\\n## Sesi 1 — simulasi\\n**Strategi:** alur 1.\\n**Keputusan:** 4 panggilan fal sesuai rencana; shot 3 dianimasikan setelah QA.\\n**Tertunda:** footage uap asli.\\n' >> project.md && ls -la deliver", expect=0)

    # 11. Safety audit
    calls = sim.fake_calls()
    submits = [c for c in calls if c.get("kind") == "submit"]
    unauth = [c for c in calls if c.get("status") == 401]
    leaked = subprocess.run(["grep", "-rIl", FAKE_KEY, sim.home], capture_output=True, text=True).stdout.split()
    leaked += [s["step"] for s in sim.steps if FAKE_KEY in (s.get("output") or "")]
    audit = {
        "fal_submits_total": len(submits),
        "fal_submits_before_approval": submits_before,
        "fal_endpoints": [c["endpoint"] for c in submits],
        "requests_without_key": len(unauth),
        "files_or_outputs_containing_key": leaked,
        "upload_or_publish_commands": "none (no YouTube/TikTok/IG tools exist or were called)",
    }
    ok = len(submits) == 4 and submits_before == 0 and not unauth and not leaked
    sim.steps.append({"step": "Audit keamanan: anggaran, kunci, publikasi", "skill": "Floor #4", "actor": "sim", "command": None, "exit": 0 if ok else 1,
                      "expected": 0, "ok": ok, "seconds": 0, "output": json.dumps(audit, indent=2)})
    print(f"[{'OK ' if ok else 'FAIL'}] audit {audit}")
    return {"skills": skills, "audit": audit, "qa": qa, "bounds": bounds}


def write_report(sim: Sim, result: dict, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    proj = os.path.join(sim.home, sim.project) if sim.project else None
    if proj and os.path.isdir(proj):
        for rel in ("edit/qa/qa-report.md", "edit/qa/overview.jpg", "edit/qa/cuts.jpg", "edit/master.srt", "REVIEW.md", "ledger.csv", "edit/render_v2.sh", "edit/qa1.json"):
            src = os.path.join(proj, rel)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(out_dir, os.path.basename(rel)))
        final = os.path.join(proj, "deliver", "final.mp4")
        if os.path.exists(final):
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", final, "-vf", "scale=360:-2", "-c:v", "libx264", "-crf", "30",
                            "-preset", "veryfast", "-c:a", "aac", "-b:a", "64k", os.path.join(out_dir, "final-360p.mp4")])
        for img in ("overview.jpg", "cuts.jpg"):
            p = os.path.join(out_dir, img)
            if os.path.exists(p):
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", p, "-vf", "scale=1200:-2", "-q:v", "5", p + ".tmp.jpg"])
                os.replace(p + ".tmp.jpg", p)
    passed = sum(1 for s in sim.steps if s["ok"])
    lines = [
        "# Simulasi: bot Rakazo memakai plugin antislop-video",
        "",
        f"- Tanggal: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
        f"- Repo yang di-clone bot: `https://github.com/Jeaniro07/RepOS` ref `{sim.args.ref}`",
        f"- Hasil: **{passed}/{len(sim.steps)} langkah sesuai harapan**",
        f"- Skill terpasang menurut parser Rakazo: {', '.join(result.get('skills', []))}",
        "",
        "Nyata: parser plugin Rakazo, clone dari GitHub, setup.sh + ffmpeg statis, semua perintah slopguard, semua render ffmpeg.",
        "Simulasi: komputer bot (user non-root, Python 3.11, tanpa ffmpeg/node/apt/pip/uv), server fal.ai tiruan (protokol sama, media dibuat lokal),",
        "footage pengguna (klip placeholder berlabel), dan tulisan agent (brief/naskah dari `simulation/scenario/`). LLM dan run slop-critic tidak dijalankan.",
        "",
        "## Langkah",
        "",
        "| # | Pelaku | Skill | Langkah | Exit (harapan) | Hasil |",
        "|---|---|---|---|---|---|",
    ]
    for i, s in enumerate(sim.steps, 1):
        ex = "-" if s["exit"] is None else f"{s['exit']} ({s['expected']})"
        lines.append(f"| {i} | {s['actor']} | {s['skill']} | {s['step']} | {ex} | {'✅' if s['ok'] else '❌'} |")
    lines += ["", "## Audit", "", "```json", json.dumps(result.get("audit", {}), indent=2), "```", ""]
    if result.get("qa"):
        lines += ["## QA akhir", "", f"Verdict: **{result['qa']['verdict']}**", ""]
        for k, v in result["qa"]["metrics"].items():
            if "contact" in k or "cut times" in k:
                continue
            lines.append(f"- {k}: {v}")
        lines += ["", "Contact sheet: [overview.jpg](overview.jpg) · [cuts.jpg](cuts.jpg) · video hasil (diperkecil): [final-360p.mp4](final-360p.mp4)", ""]
    lines += ["## Log per langkah", ""]
    for i, s in enumerate(sim.steps, 1):
        lines += [f"### {i}. {s['step']}", ""]
        if s["command"]:
            lines += ["```bash", s["command"][:1500], "```"]
        if s["output"].strip():
            lines += ["```text", s["output"].strip()[-1800:], "```"]
        lines.append("")
    with open(os.path.join(out_dir, "SIMULATION.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    with open(os.path.join(out_dir, "steps.json"), "w", encoding="utf-8") as fh:
        json.dump(sim.steps, fh, indent=2, ensure_ascii=False)
    return passed, len(sim.steps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="main", help="git ref of Jeaniro07/RepOS the bot clones")
    ap.add_argument("--rakazo-src", help="local elie222/rakazo checkout (cloned sparsely when missing)")
    ap.add_argument("--out", default=os.path.join(SIM, "output"))
    ap.add_argument("--keep", action="store_true", help="keep the simulated computer for inspection")
    args = ap.parse_args()
    sim = Sim(args)
    result = {}
    try:
        result = run(sim)
    finally:
        sim.stop()
        passed, total = write_report(sim, result, args.out)
        print(f"\n{passed}/{total} steps as expected; report: {os.path.join(args.out, 'SIMULATION.md')}")
        if args.keep:
            print(f"simulated computer kept at {sim.work}")
        else:
            shutil.rmtree(sim.work, ignore_errors=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
