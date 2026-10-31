"""Read where a media file came from: C2PA Content Credentials and container metadata.

Format map recovered from real files (see research/RE-video-provenance.md):

  ISO BMFF (mp4/mov/m4a): a top-level `uuid` box with UUID d8fec3d6-1b0e-483c-9297-5828877ec481
    payload = version/flags (4) + purpose "manifest\\0" + merkle offset (8) + JUMBF superbox
  JUMBF: `jumb` superboxes, each led by a `jumd` description (16-byte type UUID whose first four bytes
    name the kind: c2pa store, c2ma manifest, c2as assertion store, c2cl claim, c2cs signature,
    cbor/json content), toggles byte, then a NUL-terminated label when toggles & 0x02.
  Claims and most assertions are CBOR. AI generation is declared in `c2pa.actions` / `c2pa.actions.v2`
    with digitalSourceType http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia.

Observed: Google's generator writes `c2pa.created` "Created by Google Generative AI." plus
`c2pa.edited` "Applied imperceptible SynthID watermark."; ffmpeg remux or re-encode drops the box
and rewrites ©too to "Lavf…". This module reads and reports; it does NOT verify the COSE
signature, so a manifest here is a claim, not proof.
Pure standard library; safe on hostile input (bounded reads, depth limits, no exceptions escape).
"""

from __future__ import annotations

import json
import os
import struct
from typing import Any, Dict, List, Optional, Tuple

C2PA_BMFF_UUID = bytes.fromhex("d8fec3d61b0e483c92975828877ec481")
IPTC = "http://cv.iptc.org/newscodes/digitalsourcetype/"
AI_SOURCE_TYPES = {"trainedAlgorithmicMedia", "compositeWithTrainedAlgorithmicMedia"}
SYNTHETIC_SOURCE_TYPES = {"algorithmicMedia", "compositeSynthetic", "digitalArt"}
MEDIA_EXT = {".mp4", ".mov", ".m4v", ".m4a", ".heic", ".heif", ".avif", ".jpg", ".jpeg", ".png", ".webp", ".pdf"}
BMFF_CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"udta", b"ilst"}
MAX_BOX_READ = 32 * 1024 * 1024
MAX_SCAN = 64 * 1024 * 1024

# Container fingerprints seen in real files during the analysis (value -> what it means).
ENCODER_HINTS = {
    "Google": "written by Google's video tools (seen with C2PA from Google Generative AI)",
    "Lavf": "remuxed/encoded by ffmpeg (libavformat); any C2PA credentials were dropped",
    "Twitter-vork muxer": "downloaded from X/Twitter (platform re-mux; metadata stripped)",
    "Core Media": "processed by Apple AVFoundation/Core Media",
}


# ------------------------------------------------------------------ CBOR (RFC 8949 subset)


class CBORError(ValueError):
    pass


def cbor_decode(b: bytes, i: int = 0, depth: int = 0) -> Tuple[Any, int]:
    if depth > 48:
        raise CBORError("nesting too deep")
    if i >= len(b):
        raise CBORError("truncated")
    ib = b[i]
    mt, ai = ib >> 5, ib & 31
    i += 1

    def arg(ai: int, i: int) -> Tuple[Optional[int], int]:
        if ai < 24:
            return ai, i
        widths = {24: 1, 25: 2, 26: 4, 27: 8}
        if ai in widths:
            w = widths[ai]
            if i + w > len(b):
                raise CBORError("truncated length")
            return int.from_bytes(b[i:i + w], "big"), i + w
        if ai == 31:
            return None, i
        raise CBORError("reserved additional info")

    if mt == 7:
        simple = {20: False, 21: True, 22: None, 23: None}
        if ai in simple:
            return simple[ai], i
        if ai == 25:
            h = struct.unpack(">e", b[i:i + 2])[0] if i + 2 <= len(b) else 0.0
            return h, i + 2
        if ai == 26:
            return struct.unpack(">f", b[i:i + 4])[0], i + 4
        if ai == 27:
            return struct.unpack(">d", b[i:i + 8])[0], i + 8
        if ai == 24:
            return b[i] if i < len(b) else None, i + 1
        return ai, i
    n, i = arg(ai, i)
    if mt == 0:
        return n, i
    if mt == 1:
        return -1 - (n or 0), i
    if mt in (2, 3):
        if n is None:
            parts, guard = [], 0
            while i < len(b) and b[i] != 0xFF:
                v, i = cbor_decode(b, i, depth + 1)
                parts.append(v)
                guard += 1
                if guard > 100000:
                    raise CBORError("too many chunks")
            i += 1
            return (b"".join(p for p in parts if isinstance(p, bytes)) if mt == 2 else "".join(p for p in parts if isinstance(p, str))), i
        if i + n > len(b):
            raise CBORError("truncated string")
        v = b[i:i + n]
        return (bytes(v) if mt == 2 else bytes(v).decode("utf-8", "replace")), i + n
    if mt == 4:
        out: List[Any] = []
        if n is None:
            while i < len(b) and b[i] != 0xFF:
                v, i = cbor_decode(b, i, depth + 1)
                out.append(v)
            return out, i + 1
        if n > len(b):
            raise CBORError("array longer than data")
        for _ in range(n):
            v, i = cbor_decode(b, i, depth + 1)
            out.append(v)
        return out, i
    if mt == 5:
        m: Dict[Any, Any] = {}
        if n is not None and n > len(b):
            raise CBORError("map longer than data")
        count = 0
        while (n is None and i < len(b) and b[i] != 0xFF) or (n is not None and count < n):
            k, i = cbor_decode(b, i, depth + 1)
            v, i = cbor_decode(b, i, depth + 1)
            m[k if isinstance(k, (str, int, float, bool)) or k is None else repr(k)] = v
            count += 1
        if n is None:
            i += 1
        return m, i
    # mt == 6: tag; keep the value (COSE_Sign1 is tag 18)
    v, i = cbor_decode(b, i, depth + 1)
    return {"__tag__": n, "value": v}, i


# ------------------------------------------------------------------ JUMBF


def _boxes(b: bytes, off: int, end: int):
    end = min(end, len(b))
    guard = 0
    while off + 8 <= end:
        size, typ = struct.unpack(">I4s", b[off:off + 8])
        hl = 8
        if size == 1:
            if off + 16 > end:
                return
            size = struct.unpack(">Q", b[off + 8:off + 16])[0]
            hl = 16
        elif size == 0:
            size = end - off
        if size < hl or off + size > end:
            return
        yield off, size, typ, hl
        off += size
        guard += 1
        if guard > 100000:
            return


def _jumd(b: bytes, off: int, size: int, hl: int) -> Tuple[str, Optional[str]]:
    p = b[off + hl:off + size]
    if len(p) < 17:
        return "", None
    kind = p[:4].decode("latin1", "replace")
    toggles = p[16]
    label = None
    if toggles & 0x02:
        nul = p.find(b"\x00", 17)
        if nul > 0:
            label = p[17:nul].decode("utf-8", "replace")
    return kind, label


def _content(b: bytes, kids) -> Tuple[Optional[str], Any]:
    """Decode the first content box of a JUMBF superbox."""
    for o, size, typ, hl in kids:
        payload = b[o + hl:o + size]
        if typ == b"cbor":
            try:
                return "cbor", cbor_decode(payload)[0]
            except (CBORError, IndexError, struct.error, ValueError):
                return "cbor", None
        if typ == b"json":
            try:
                return "json", json.loads(payload.decode("utf-8", "replace"))
            except ValueError:
                return "json", None
        if typ in (b"bidb", b"uuid"):
            return typ.decode(), None
    return None, None


def _walk_superbox(b: bytes, off: int, size: int, hl: int, depth: int = 0) -> Optional[Dict[str, Any]]:
    if depth > 12:
        return None
    kids = list(_boxes(b, off + hl, off + size))
    if not kids or kids[0][2] != b"jumd":
        return None
    kind, label = _jumd(b, kids[0][0], kids[0][1], kids[0][3])
    node: Dict[str, Any] = {"kind": kind, "label": label, "size": size, "children": []}
    rest = kids[1:]
    for o, s, t, h in rest:
        if t == b"jumb":
            child = _walk_superbox(b, o, s, h, depth + 1)
            if child:
                node["children"].append(child)
    if not node["children"]:
        node["content_type"], node["content"] = _content(b, rest)
    return node


def parse_jumbf(b: bytes) -> Optional[Dict[str, Any]]:
    for o, size, typ, hl in _boxes(b, 0, len(b)):
        if typ == b"jumb":
            return _walk_superbox(b, o, size, hl)
    return None


# ------------------------------------------------------------------ C2PA interpretation


def _short(v: Any, limit: int = 300) -> Any:
    if isinstance(v, bytes):
        return f"<{len(v)} bytes>"
    if isinstance(v, str):
        return v if len(v) <= limit else v[: limit - 1] + "…"
    if isinstance(v, dict):
        return {str(k): _short(x, limit) for k, x in v.items()}
    if isinstance(v, list):
        return [_short(x, limit) for x in v[:50]]
    return v


def _source_kind(dst: Optional[str]) -> Optional[str]:
    if not isinstance(dst, str):
        return None
    term = dst.rsplit("/", 1)[-1]
    if term in AI_SOURCE_TYPES:
        return "ai"
    if term in SYNTHETIC_SOURCE_TYPES:
        return "synthetic"
    return "other"


def interpret_store(store: Dict[str, Any]) -> Dict[str, Any]:
    manifests = []
    for m in store.get("children", []):
        if m.get("kind") not in ("c2ma", "c2um"):
            continue
        info: Dict[str, Any] = {"label": m.get("label"), "assertions": [], "actions": [], "claim": None, "signed": False}
        for part in m.get("children", []):
            k = part.get("kind")
            if k == "c2cs":
                info["signed"] = True
            elif k == "c2cl":
                claim = part.get("content") if isinstance(part.get("content"), dict) else {}
                gen = claim.get("claim_generator")
                gi = claim.get("claim_generator_info")
                if isinstance(gi, dict):
                    gi = [gi]
                info["claim"] = {
                    "version": "v2" if (part.get("label") or "").endswith(".v2") else "v1",
                    "claim_generator": gen,
                    "claim_generator_info": [_short(x) for x in gi] if isinstance(gi, list) else None,
                    "title": claim.get("dc:title") or claim.get("title"),
                    "format": claim.get("dc:format"),
                    "instanceID": claim.get("instanceID"),
                }
            elif k == "c2as":
                for a in part.get("children", []):
                    label = a.get("label") or ""
                    info["assertions"].append(label)
                    if label.startswith("c2pa.actions"):
                        data = a.get("content") if isinstance(a.get("content"), dict) else {}
                        for act in data.get("actions", []) or []:
                            if not isinstance(act, dict):
                                continue
                            dst = act.get("digitalSourceType")
                            agent = act.get("softwareAgent")
                            if isinstance(agent, dict):
                                agent = agent.get("name")
                            info["actions"].append({
                                "action": act.get("action"),
                                "digitalSourceType": dst,
                                "source_kind": _source_kind(dst),
                                "softwareAgent": agent,
                                "description": act.get("description"),
                            })
        manifests.append(info)
    active = manifests[-1] if manifests else None  # the active manifest is the last in the store
    ai_active = bool(active and any(a["source_kind"] == "ai" for a in active["actions"]))
    ai_any = any(a["source_kind"] == "ai" for m in manifests for a in m["actions"])
    generators = []
    for m in manifests:
        c = m.get("claim") or {}
        if c.get("claim_generator"):
            generators.append(str(c["claim_generator"]))
        for gi in c.get("claim_generator_info") or []:
            if isinstance(gi, dict) and gi.get("name"):
                generators.append(str(gi["name"]) + (f" {gi['version']}" if gi.get("version") else ""))
        for a in m["actions"]:
            if a.get("softwareAgent"):
                generators.append(str(a["softwareAgent"]))
    return {
        "manifests": manifests,
        "active_manifest": active["label"] if active else None,
        "ai_generated": ai_active,
        "ai_in_history": ai_any,
        "generators": sorted(set(generators)),
    }


# ------------------------------------------------------------------ containers


def _bmff(path: str, f, size: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {"container": "iso-bmff", "brands": [], "top_boxes": [], "uuid_boxes": [], "tags": {}, "handlers": [], "c2pa_raw": None}

    def walk(off: int, end: int, depth: int):
        guard = 0
        while off + 8 <= end and guard < 20000:
            guard += 1
            f.seek(off)
            h = f.read(16)
            if len(h) < 8:
                return
            bsize, typ = struct.unpack(">I4s", h[:8])
            hl = 8
            if bsize == 1:
                if len(h) < 16:
                    return
                bsize = struct.unpack(">Q", h[8:16])[0]
                hl = 16
            elif bsize == 0:
                bsize = end - off
            if bsize < hl or off + bsize > end:
                return
            if depth == 0:
                out["top_boxes"].append(typ.decode("latin1"))
            if typ == b"ftyp" and depth == 0:
                f.seek(off + hl)
                d = f.read(min(bsize - hl, 64))
                out["brands"] = [d[:4].decode("latin1")] + [d[i:i + 4].decode("latin1") for i in range(8, len(d) - 3, 4)]
            elif typ == b"uuid":
                f.seek(off + hl)
                u = f.read(16)
                out["uuid_boxes"].append({"offset": off, "uuid": u.hex(), "size": bsize})
                if u == C2PA_BMFF_UUID and out["c2pa_raw"] is None and bsize <= MAX_BOX_READ:
                    f.seek(off + hl + 16)
                    out["c2pa_raw"] = (off, f.read(bsize - hl - 16))
            elif typ == b"meta":
                f.seek(off + hl)
                peek = f.read(8)
                inner = off + hl + (0 if peek[4:8] == b"hdlr" else 4)  # QuickTime meta has no version/flags
                walk(inner, off + bsize, depth + 1)
            elif typ == b"hdlr" and bsize <= 4096:
                f.seek(off + hl + 24)
                name = f.read(bsize - hl - 24).split(b"\x00")[0]
                name = name.lstrip(bytes(range(32)))  # QuickTime writers may prefix a length byte
                if name.strip():
                    out["handlers"].append(name.decode("utf-8", "replace").strip())
            elif depth >= 1 and (typ[:1] == b"\xa9") and bsize <= 4096:
                f.seek(off + hl)
                payload = f.read(bsize - hl)
                k = payload.find(b"data")
                val = payload[k + 12:] if k >= 4 else payload[4:]
                out["tags"][typ.decode("latin1")] = val.decode("utf-8", "replace").strip("\x00 ")
            elif typ in BMFF_CONTAINERS and depth < 8:
                walk(off + hl, off + bsize, depth + 1)
            off += bsize

    walk(0, size, 0)
    return out


def _scan_jumbf(f, size: int) -> Optional[Tuple[int, bytes]]:
    """Fallback for non-BMFF files (JPEG APP11, PNG caBX, PDF streams...): find a c2pa JUMBF superbox."""
    f.seek(0)
    data = f.read(min(size, MAX_SCAN))
    start = 0
    while True:
        k = data.find(b"jumb", start)
        if k < 4:
            return None
        box_start = k - 4
        bsize = struct.unpack(">I", data[box_start:k])[0]
        if data[k + 8:k + 12] == b"jumd" and data[k + 12:k + 16] == b"c2pa" and 16 < bsize <= len(data) - box_start:
            return box_start, data[box_start:box_start + bsize]
        start = k + 4


def inspect(path: str) -> Dict[str, Any]:
    """Provenance facts for one file. Never raises on malformed input."""
    result: Dict[str, Any] = {"path": path, "c2pa": False, "ai_generated": False, "ai_in_history": False, "generators": [], "hints": []}
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            head = f.read(12)
            if head[4:8] == b"ftyp":
                meta = _bmff(path, f, size)
                raw = meta.pop("c2pa_raw")
                result.update(meta)
                if raw:
                    off, p = raw
                    nul = p.find(b"\x00", 4)
                    purpose = p[4:nul].decode("latin1", "replace") if nul > 0 else ""
                    result["c2pa_box"] = {"offset": off, "purpose": purpose}
                    jumbf = p[nul + 1 + 8:] if nul > 0 else b""
                    store = parse_jumbf(jumbf)
                    if store and store.get("kind") == "c2pa":
                        result["c2pa"] = True
                        result.update(interpret_store(store))
            else:
                result["container"] = "other"
                found = _scan_jumbf(f, size)
                if found:
                    off, blob = found
                    store = parse_jumbf(blob)
                    if store and store.get("kind") == "c2pa":
                        result["c2pa"] = True
                        result["c2pa_box"] = {"offset": off, "purpose": "embedded"}
                        result.update(interpret_store(store))
    except (OSError, struct.error, ValueError, IndexError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    for value in dict.fromkeys(list(result.get("tags", {}).values()) + list(result.get("handlers", []))):
        for key, meaning in ENCODER_HINTS.items():
            if isinstance(value, str) and value.startswith(key):
                result["hints"].append(f"{value}: {meaning}")
    return result


def summarize(info: Dict[str, Any]) -> str:
    lines = [f"{info['path']}"]
    if info.get("error"):
        lines.append(f"  error: {info['error']}")
    if info.get("container") == "iso-bmff":
        lines.append(f"  container: ISO BMFF, brands {', '.join(info.get('brands') or [])}; boxes {' '.join(info.get('top_boxes') or [])}")
    tags = info.get("tags") or {}
    if tags:
        lines.append("  tags: " + ", ".join(f"{k}={v}" for k, v in tags.items()))
    if info.get("handlers"):
        lines.append("  handlers: " + ", ".join(info["handlers"]))
    if info.get("c2pa"):
        lines.append(f"  C2PA Content Credentials: yes (at offset {info['c2pa_box']['offset']}; signature NOT verified by slopguard)")
        lines.append(f"  active manifest: {info.get('active_manifest')}")
        if info.get("generators"):
            lines.append("  generator(s): " + "; ".join(info["generators"]))
        for m in info.get("manifests", []):
            for a in m["actions"]:
                dst = (a.get("digitalSourceType") or "").rsplit("/", 1)[-1]
                lines.append(f"  action: {a.get('action')}  source={dst or '-'}  {a.get('description') or a.get('softwareAgent') or ''}".rstrip())
        verdict = "declares AI-generated content" if info.get("ai_generated") else (
            "AI content in its history (ingredient)" if info.get("ai_in_history") else "no AI declaration")
        lines.append(f"  => {verdict}")
    else:
        lines.append("  C2PA Content Credentials: none found")
    for h in info.get("hints", []):
        lines.append(f"  hint: {h}")
    return "\n".join(lines)


def media_files(root: str, limit: int = 300) -> List[str]:
    out: List[str] = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith(".") and d not in ("qa", "clips", "frames", "cut-frames", "safe-frames")]
        for name in sorted(fn):
            if os.path.splitext(name)[1].lower() in MEDIA_EXT:
                out.append(os.path.join(dp, name))
                if len(out) >= limit:
                    return out
    return out
