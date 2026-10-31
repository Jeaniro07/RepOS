"""`slopguard init`: scaffold a video project folder.

<project>/
  slopguard.json   format, duration, language, loudness, fal budget
  BRIEF.md         who it is for, the one thing they should get, the material
  SPEC.md          every adjective turned into a number + the BANNED list
  script.md        narration with [n] citations and a Sources section
  ledger.csv       one row per shot: idea, visual, source, license
  waivers.json     REFLEX gates waived on purpose, each with a reason
  project.md       session memory, appended every session
  assets/          inputs the user gave (never modified)
  gen/             generated media (fal outputs), with their result JSON
  edit/            renders, captions, QA reports, contact sheets
"""

from __future__ import annotations

import json
import os
import time

FORMATS = {
    "vertical": ("1080x1920", 30),
    "landscape": ("1920x1080", 30),
    "square": ("1080x1080", 30),
    "portrait45": ("1080x1350", 30),
}

BRIEF = """# Brief: {title}

> Diisi bersama pengguna SEBELUM menulis naskah. Satu kali tanya, maksimal 5 pertanyaan.

- **Untuk siapa (satu penonton spesifik):**
- **Satu hal yang harus mereka dapat / lakukan setelah menonton:**
- **Kenapa video ini perlu ada (apa yang belum ada di luar sana):**
- **Platform & format:** {format} ({size}), target {duration}s, bahasa narasi `{lang}`
- **Bahan nyata yang tersedia (footage, layar produk, foto, data, kutipan):**
- **Sumber fakta (link/dokumen):**
- **Suara/brand (kata yang dipakai & yang dilarang):**
- **Batas biaya fal.ai untuk proyek ini:** {max_calls} panggilan (ubah di slopguard.json hanya atas izin pengguna)
- **Yang TIDAK boleh terjadi:**

## Tiga alur cerita (pilih satu)
1.
2.
3.
"""

SPEC = """# SPEC: {title}

Setiap kata sifat diganti angka. Dibangun dari sini, dicek terhadap ini.

GOAL:    (apa yang penonton rasakan/lakukan di akhir, satu kalimat)
OUTPUT:  {size} @ {fps} fps, {duration}s, -14 LUFS, true peak <= -1 dBTP
HOOK:    (0-3 detik pertama: gambar apa di frame 0, kalimat apa, kenapa tidak di-skip)
LOOK:    (latar hex + tekstur, tinta, satu warna aksen & di mana boleh muncul;
          font display + ukuran px, font body; medium: footage / layar produk / kertas / clay ...)
TYPE:    teks yang dibaca >= 2.6% sisi pendek frame (>= 28 px pada 1080), tahan 0.5 s + 0.3 s per kata
MOTION:  easing per peran (masuk, gerak, keluar, kamera), durasi dalam frame; satu gerakan utama per shot
SOUND:   narasi (suara apa), musik (ya/tidak, -12..-15 dB di bawah suara), SFX hanya pada aksi yang terlihat
SHOTS:   satu baris per shot: rentang waktu | aksi utama | apa yang dibaca penonton | suara | transisi
BANNED:  (default yang dilarang; tambahkan setiap default yang muncul di render pertama)
  - latar void gelap dengan elemen kecil melayang di tengah
  - glow/bloom/neon/partikel dekoratif, gradien ungu-biru, kartu kaca
  - semua elemen fade + slide up; judul yang terus bergerak setelah mendarat
  - zoom pelan (Ken Burns) di atas gambar AI sebagai pengganti cerita
  - potongan tiap N detik tetap seperti metronom
  - stok b-roll generik yang tidak menjelaskan narasi
  - emoji sebagai ikon, teks caption penuh emoji
  - suara TTS datar tanpa jeda; musik "hype" default
QA:      (frame mana yang dicek dan apa yang harus terlihat di sana)
"""

SCRIPT = """# Naskah: {title}

> Tulis seperti diucapkan. Satu klaim per kalimat. Setiap fakta/angka diberi [n].
> Catatan visual di dalam [VISUAL: ...] tidak dihitung sebagai narasi.

[VISUAL: frame 0 — hook image]
(kalimat pembuka: hal paling spesifik dan benar yang kamu punya)

Sumber:
[1] judul, penerbit, tanggal, URL
"""

LEDGER_HEADER = "shot,start,end,narration,idea,visual,source_type,source,license,real_person,notes\n"

PROJECT_MD = """# {title}

Memori proyek. Tambahkan satu bagian per sesi; baca bagian terakhir sebelum melanjutkan.

## Sesi 1 — {date}

**Strategi:**
**Keputusan:**
**Alasan non-obvious:**
**Tertunda:**
"""


def init_project(path: str, title: str, fmt: str = "vertical", duration: int = 45, lang: str = "id", max_calls: int = 12) -> list:
    if fmt not in FORMATS:
        raise ValueError(f"format must be one of {', '.join(FORMATS)}")
    size, fps = FORMATS[fmt]
    os.makedirs(path, exist_ok=True)
    for d in ("assets", "gen", "edit"):
        os.makedirs(os.path.join(path, d), exist_ok=True)
    ctx = dict(title=title, format=fmt, size=size, fps=fps, duration=duration, lang=lang, max_calls=max_calls, date=time.strftime("%Y-%m-%d"))
    files = {
        "slopguard.json": json.dumps(
            {
                "title": title,
                "format": fmt,
                "target": size,
                "fps": fps,
                "duration": duration,
                "lang": lang,
                "lufs": -14,
                "fal": {"max_calls": max_calls},
                "lexicon": {"extra": []},
            },
            indent=2,
        )
        + "\n",
        "BRIEF.md": BRIEF.format(**ctx),
        "SPEC.md": SPEC.format(**ctx),
        "script.md": SCRIPT.format(**ctx),
        "ledger.csv": LEDGER_HEADER,
        "waivers.json": json.dumps({"waivers": []}, indent=2) + "\n",
        "project.md": PROJECT_MD.format(**ctx),
    }
    written = []
    for name, content in files.items():
        dest = os.path.join(path, name)
        if os.path.exists(dest):
            continue  # never overwrite the user's work
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(content)
        written.append(dest)
    return written


def load_config(start: str) -> dict:
    cur = os.path.abspath(start if os.path.isdir(start) else os.path.dirname(start) or ".")
    while True:
        cfg = os.path.join(cur, "slopguard.json")
        if os.path.exists(cfg):
            with open(cfg, encoding="utf-8") as fh:
                data = json.load(fh)
            data["_root"] = cur
            return data
        parent = os.path.dirname(cur)
        if parent == cur:
            return {}
        cur = parent
