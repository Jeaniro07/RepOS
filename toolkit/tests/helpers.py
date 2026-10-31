"""Synthetic test media built with ffmpeg's lavfi sources."""

from __future__ import annotations

import os
import shutil
import subprocess

FFMPEG = shutil.which("ffmpeg")


def _run(args):
    subprocess.run([FFMPEG, "-nostdin", "-hide_banner", "-loglevel", "error", "-y"] + args, check=True, stdin=subprocess.DEVNULL)


def make_sloppy(path: str, size: str = "540x960") -> str:
    """1.5 s black, 5 s frozen flat card, 8 s motion; audio clips and has a 4 s hole."""
    _run(
        [
            "-f", "lavfi", "-i", f"color=c=black:s={size}:r=30:d=1.5",
            "-f", "lavfi", "-i", f"color=c=0x4682b4:s={size}:r=30:d=5",
            "-f", "lavfi", "-i", f"testsrc2=s={size}:r=30:d=8",
            "-f", "lavfi", "-i", "aevalsrc=0.999*sin(2*PI*440*t)*(lt(t\\,6)+gt(t\\,10)):s=48000:d=14.5",
            "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]",
            "-map", "[v]", "-map", "3:a", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest", path,
        ]
    )
    return path


def make_clean(path: str, size: str = "540x960") -> str:
    """Moving picture with irregular cuts, steady audio normalised near -14 LUFS."""
    durs = [3.3, 1.9, 4.6, 2.4, 3.8]
    srcs = [
        f"testsrc2=s={size}:r=30:d={durs[0]}",
        f"mandelbrot=s={size}:r=30,trim=duration={durs[1]}",
        f"testsrc=s={size}:r=30:d={durs[2]},hue=h=t*40",
        f"life=s={size}:r=30:mold=10:ratio=0.2:death_color=#c83232:life_color=#00ff88,trim=duration={durs[3]}",
        f"rgbtestsrc=s={size}:r=30:d={durs[4]},rotate=a=t:fillcolor=0x202020",
    ]
    args = []
    for s in srcs:
        args += ["-f", "lavfi", "-i", s]
    total = sum(durs)
    args += ["-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.25:d={total}:r=48000"]
    chains = "".join(f"[{i}:v]scale={size},setsar=1,fps=30,format=yuv420p[v{i}];" for i in range(len(srcs)))
    concat = "".join(f"[v{i}]" for i in range(len(srcs))) + f"concat=n={len(srcs)}:v=1:a=0[v];"
    audio = f"[{len(srcs)}:a]lowpass=f=3500,loudnorm=I=-14:TP=-2:LRA=7[a]"
    _run(
        args
        + [
            "-filter_complex", chains + concat + audio,
            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{total}", path,
        ]
    )
    return path


def make_metronomic(path: str, size: str = "540x960", shots: int = 8, shot_len: float = 2.0) -> str:
    """Alternating sources cut on an exact timer."""
    args = []
    for i in range(shots):
        src = "testsrc2" if i % 2 == 0 else "testsrc"
        args += ["-f", "lavfi", "-i", f"{src}=s={size}:r=30:d={shot_len},hue=h={i * 45}"]
    total = shots * shot_len
    args += ["-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.25:d={total}:r=48000"]
    chains = "".join(f"[{i}:v]format=yuv420p[v{i}];" for i in range(shots))
    concat = "".join(f"[v{i}]" for i in range(shots)) + f"concat=n={shots}:v=1:a=0[v];"
    audio = f"[{shots}:a]loudnorm=I=-14:TP=-2[a]"
    _run(args + ["-filter_complex", chains + concat + audio, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", path])
    return path


def make_flicker(path: str, size: str = "540x960", seconds: float = 4.0) -> str:
    """Moving picture whose brightness flips up/down every frame (generated-video flicker)."""
    _run(
        [
            "-f", "lavfi", "-i", f"testsrc2=s={size}:r=30:d={seconds}",
            "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.25:d={seconds}:r=48000",
            "-vf", "eq=eval=frame:brightness='0.008*(2*mod(n,2)-1)',format=yuv420p",
            "-af", "loudnorm=I=-14:TP=-2", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-c:a", "aac", path,
        ]
    )
    return path


def have_ffmpeg() -> bool:
    return FFMPEG is not None and os.access(FFMPEG, os.X_OK)


# ---------------------------------------------------------------- synthetic C2PA (mirrors real Google/Truepic layouts)

JUMBF_SUFFIX = bytes.fromhex("00110010800000aa00389b71")
C2PA_UUID = bytes.fromhex("d8fec3d61b0e483c92975828877ec481")


def cbor_encode(v) -> bytes:
    import struct as _s

    def head(mt, n):
        if n < 24:
            return bytes([mt << 5 | n])
        for ai, w in ((24, 1), (25, 2), (26, 4), (27, 8)):
            if n < 1 << (8 * w):
                return bytes([mt << 5 | ai]) + n.to_bytes(w, "big")
        raise ValueError(n)
    if v is True:
        return b"\xf5"
    if v is False:
        return b"\xf4"
    if v is None:
        return b"\xf6"
    if isinstance(v, int):
        return head(0, v) if v >= 0 else head(1, -1 - v)
    if isinstance(v, float):
        return b"\xfb" + _s.pack(">d", v)
    if isinstance(v, bytes):
        return head(2, len(v)) + v
    if isinstance(v, str):
        b = v.encode()
        return head(3, len(b)) + b
    if isinstance(v, (list, tuple)):
        return head(4, len(v)) + b"".join(cbor_encode(x) for x in v)
    if isinstance(v, dict):
        return head(5, len(v)) + b"".join(cbor_encode(k) + cbor_encode(x) for k, x in v.items())
    raise TypeError(type(v))


def _box(typ: bytes, payload: bytes) -> bytes:
    return (8 + len(payload)).to_bytes(4, "big") + typ + payload


def jumbf(kind: str, label: str, content: bytes = b"", children=()) -> bytes:
    jumd = _box(b"jumd", kind.encode() + JUMBF_SUFFIX + b"\x03" + label.encode() + b"\x00")
    return _box(b"jumb", jumd + content + b"".join(children))


def c2pa_store(actions, generator="Test Generator", label="urn:c2pa:test-0001") -> bytes:
    assertion = jumbf("cbor", "c2pa.actions.v2", _box(b"cbor", cbor_encode({"actions": actions})))
    claim = jumbf("c2cl", "c2pa.claim.v2", _box(b"cbor", cbor_encode({
        "instanceID": "xmp:iid:test", "claim_generator_info": {"name": generator, "version": "1"},
        "created_assertions": [{"url": "self#jumbf=c2pa.assertions/c2pa.actions.v2", "hash": b"\x00" * 32}],
        "signature": "self#jumbf=c2pa.signature", "alg": "sha256",
    })))
    signature = jumbf("c2cs", "c2pa.signature", _box(b"cbor", b"\xd2\x84\x40\xa0\xf6\x40"))
    manifest = jumbf("c2ma", label, children=[signature, claim, jumbf("c2as", "c2pa.assertions", children=[assertion])])
    return jumbf("c2pa", "c2pa", children=[manifest])


def add_c2pa(src: str, dst: str, store: bytes) -> str:
    """Append a top-level C2PA uuid box (appending keeps every chunk offset valid)."""
    payload = C2PA_UUID + b"\x00\x00\x00\x00" + b"manifest\x00" + b"\x00" * 8 + store
    with open(src, "rb") as fh:
        data = fh.read()
    with open(dst, "wb") as fh:
        fh.write(data + _box(b"uuid", payload))
    return dst


AI = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
CAMERA = "http://cv.iptc.org/newscodes/digitalsourcetype/digitalCapture"
