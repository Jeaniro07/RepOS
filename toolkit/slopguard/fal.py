"""Minimal fal.ai queue client (standard library only).

Protocol (from fal's docs and the official fal-client source):
  submit   POST https://queue.fal.run/<endpoint_id>        -> {request_id, status_url, response_url, cancel_url}
  status   GET  <status_url>?logs=1                        -> {status: IN_QUEUE|IN_PROGRESS|COMPLETED, ...}
  result   GET  <response_url>                             -> model-specific JSON
  upload   POST https://rest.fal.ai/storage/upload/initiate?storage_type=gcs  {file_name, content_type}
           -> {upload_url, file_url}; then PUT the bytes to upload_url.
Auth header: "Authorization: Key $FAL_KEY".

Spending guard: every run needs confirm=True (CLI: --confirm) and counts
against a per-project call budget (slopguard.json -> fal.max_calls,
default 12). Every call is appended to .slopguard/fal-calls.jsonl.
The key is read from the environment and never printed or logged.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

QUEUE_BASE = os.environ.get("FAL_QUEUE_BASE", "https://queue.fal.run")
REST_BASE = os.environ.get("FAL_REST_BASE", "https://rest.fal.ai")
USER_AGENT = "slopguard/0.1 (+https://github.com/Jeaniro07/RepOS)"
DEFAULT_MAX_CALLS = 12
ENDPOINT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*(/[a-zA-Z0-9._-]+)+$")


class FalError(RuntimeError):
    pass


def _key() -> str:
    key = os.environ.get("FAL_KEY", "").strip()
    if not key:
        raise FalError(
            "FAL_KEY is not set. In Rakazo, save it as a command variable named 'fal-key' "
            "(request_secret with auth type 'command'); it is then exported as $FAL_KEY."
        )
    return key


def _request(method: str, url: str, body: Optional[bytes] = None, headers: Optional[dict] = None, auth: bool = True, timeout: int = 60) -> Tuple[int, bytes]:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if auth:
        h["Authorization"] = f"Key {_key()}"
    h.update(headers or {})
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:2000].decode("utf-8", "replace")
        raise FalError(f"{method} {_redact(url)} -> HTTP {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise FalError(f"{method} {_redact(url)} failed: {exc.reason}") from None


def _redact(url: str) -> str:
    return re.sub(r"(key|token)=[^&]+", r"\1=***", url, flags=re.I)


def _json(method: str, url: str, payload: Any = None, timeout: int = 60) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    _, data = _request(method, url, body, headers, timeout=timeout)
    try:
        return json.loads(data or b"{}")
    except json.JSONDecodeError:
        raise FalError(f"Non-JSON response from {_redact(url)}: {data[:300]!r}") from None


# ------------------------------------------------------------- budget


def _project_root(start: str) -> str:
    cur = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(cur, "slopguard.json")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return os.path.abspath(start)
        cur = parent


def budget(project_dir: str) -> Tuple[int, int, str]:
    """(calls_used, max_calls, log_path)"""
    root = _project_root(project_dir)
    max_calls = DEFAULT_MAX_CALLS
    cfg = os.path.join(root, "slopguard.json")
    if os.path.exists(cfg):
        try:
            with open(cfg, encoding="utf-8") as fh:
                max_calls = int(json.load(fh).get("fal", {}).get("max_calls", DEFAULT_MAX_CALLS))
        except (ValueError, json.JSONDecodeError):
            pass
    log = os.path.join(root, ".slopguard", "fal-calls.jsonl")
    used = 0
    if os.path.exists(log):
        with open(log, encoding="utf-8") as fh:
            used = sum(1 for line in fh if '"event": "submit"' in line)
    return used, max_calls, log


def _log(log_path: str, entry: dict) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    entry = dict(entry, ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ------------------------------------------------------------- upload


def upload_file(path: str) -> str:
    """Upload a local file to fal storage and return its URL."""
    if not os.path.exists(path):
        raise FalError(f"File not found: {path}")
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    name = os.path.basename(path)
    init = _json(
        "POST",
        f"{REST_BASE}/storage/upload/initiate?storage_type=gcs",
        {"file_name": name, "content_type": ctype},
    )
    upload_url, file_url = init.get("upload_url"), init.get("file_url")
    if not upload_url or not file_url:
        raise FalError(f"Unexpected upload response: {list(init)}")
    with open(path, "rb") as fh:
        data = fh.read()
    _request("PUT", upload_url, data, {"Content-Type": ctype}, auth=False, timeout=600)
    return file_url


def data_uri(path: str) -> str:
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as fh:
        return f"data:{ctype};base64,{base64.b64encode(fh.read()).decode()}"


def resolve_local_inputs(payload: Any, base_dir, inline_max_bytes: int = 0) -> Any:
    """Replace values of *_url / *_urls keys that point at local files with uploaded URLs.
    base_dir may be one folder or a list tried in order (input file's folder, then cwd)."""
    if isinstance(payload, dict):
        out = {}
        for k, v in payload.items():
            if (k.endswith("_url") or k.endswith("_urls") or k in ("image", "audio", "video")) and v:
                out[k] = _resolve_value(v, base_dir, inline_max_bytes)
            else:
                out[k] = resolve_local_inputs(v, base_dir, inline_max_bytes)
        return out
    if isinstance(payload, list):
        return [resolve_local_inputs(v, base_dir, inline_max_bytes) for v in payload]
    return payload


def _resolve_value(v: Any, base_dir: str, inline_max_bytes: int) -> Any:
    if isinstance(v, list):
        return [_resolve_value(x, base_dir, inline_max_bytes) for x in v]
    if isinstance(v, str) and not re.match(r"^(https?:|data:)", v):
        bases = base_dir if isinstance(base_dir, (list, tuple)) else [base_dir]
        candidates = [v] if os.path.isabs(v) else [os.path.join(b, v) for b in bases]
        p = next((c for c in candidates if os.path.exists(c)), None)
        if p:
            if inline_max_bytes and os.path.getsize(p) <= inline_max_bytes:
                return data_uri(p)
            return upload_file(p)
    return v


def payload_has_no_local_paths(payload: Any, bases) -> bool:
    """After resolution, every *_url value must be a URL (or data URI)."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            if (k.endswith("_url") or k.endswith("_urls")) and v:
                vals = v if isinstance(v, list) else [v]
                if any(isinstance(x, str) and not re.match(r"^(https?:|data:)", x) for x in vals):
                    return False
            elif not payload_has_no_local_paths(v, bases):
                return False
    elif isinstance(payload, list):
        return all(payload_has_no_local_paths(x, bases) for x in payload)
    return True


# ------------------------------------------------------------- run


def submit(endpoint: str, payload: dict) -> dict:
    if not ENDPOINT_RE.match(endpoint):
        raise FalError(f"'{endpoint}' does not look like a fal endpoint id (owner/app[/path]).")
    return _json("POST", f"{QUEUE_BASE}/{endpoint}", payload)


def wait(handle: dict, max_wait: int = 900, poll: float = 3.0, on_status=None) -> dict:
    status_url = handle.get("status_url")
    response_url = handle.get("response_url")
    if not status_url or not response_url:
        raise FalError("Submit response has no status_url/response_url.")
    deadline = time.time() + max_wait
    last = None
    while time.time() < deadline:
        st = _json("GET", status_url + ("&" if "?" in status_url else "?") + "logs=1")
        status = st.get("status")
        if status != last and on_status:
            on_status(status, st)
        last = status
        if status == "COMPLETED":
            if st.get("error"):
                raise FalError(f"Request failed: {st.get('error')}")
            return _json("GET", response_url, timeout=120)
        time.sleep(poll)
        poll = min(poll * 1.3, 15.0)
    raise FalError(
        f"Timed out after {max_wait}s (last status {last}). Resume later with: "
        f"slopguard fal result --response-url '{response_url}'"
    )


def collect_urls(obj: Any, prefix: str = "") -> List[Tuple[str, str]]:
    """Find every media URL in a result: [(json_path, url)]."""
    found: List[Tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, str) and k in ("url", "file_url", "video_url", "audio_url", "image_url") and v.startswith("http"):
                found.append((path, v))
            else:
                found.extend(collect_urls(v, path))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(collect_urls(v, f"{prefix}[{i}]"))
    return found


def download(url: str, out_dir: str, stem: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    parsed = urllib.parse.urlparse(url)
    ext = os.path.splitext(parsed.path)[1] or ".bin"
    dest = os.path.abspath(os.path.join(out_dir, f"{stem}{ext}"))  # absolute: safe to pass to the next step
    _, data = _request("GET", url, auth=False, timeout=600)
    with open(dest, "wb") as fh:
        fh.write(data)
    return dest


def run(
    endpoint: str,
    payload: dict,
    out_dir: str,
    project_dir: str = ".",
    confirm: bool = False,
    max_wait: int = 900,
    label: str = "",
    on_status=None,
    base_dir=None,
) -> dict:
    used, max_calls, log = budget(project_dir)
    if not confirm:
        raise FalError(
            f"Paid generation needs --confirm. Budget: {used}/{max_calls} calls used in this project. "
            "Get the user's approval for this call (endpoint, inputs, expected cost) first."
        )
    if used >= max_calls:
        raise FalError(
            f"Call budget reached ({used}/{max_calls}). Ask the user before raising fal.max_calls in slopguard.json."
        )
    _key()
    bases = [b for b in ([base_dir] if isinstance(base_dir, str) else list(base_dir or [])) if b] + [os.getcwd()]
    payload = resolve_local_inputs(payload, bases)
    if not payload_has_no_local_paths(payload, bases):
        raise FalError("An input *_url points at a local path that does not exist. Use a path relative to the project folder, or a URL.")
    handle = submit(endpoint, payload)
    _log(log, {"event": "submit", "endpoint": endpoint, "request_id": handle.get("request_id"), "label": label})
    result = wait(handle, max_wait=max_wait, on_status=on_status)
    os.makedirs(out_dir, exist_ok=True)
    rid = handle.get("request_id", "result")
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", label or endpoint.split("/")[-1])[:40].strip("-") or "fal"
    with open(os.path.join(out_dir, f"{safe}-{rid[:8]}.json"), "w", encoding="utf-8") as fh:
        json.dump({"endpoint": endpoint, "request_id": rid, "input": payload, "result": result}, fh, indent=2)
    files = []
    for i, (path, url) in enumerate(collect_urls(result)):
        try:
            files.append(download(url, out_dir, f"{safe}-{rid[:8]}-{i}"))
        except FalError as exc:
            files.append(f"(download failed: {exc})")
    _log(log, {"event": "done", "endpoint": endpoint, "request_id": rid, "files": files})
    return {"request_id": rid, "files": files, "result": result}


# ------------------------------------------------------------- plan


def plan_table(plan: dict, project_dir: str = ".") -> Tuple[str, dict]:
    """Render a generation plan for the user's approval.

    plan.json: {"currency": "USD", "items": [{"endpoint": "...", "purpose": "shot 4 still",
      "count": 1, "unit": "image|second|minute|call", "quantity": 1, "unit_price": 0.15,
      "price_source": "fal model page, 2026-10-31"}]}
    Prices are what the agent read on the model page; this never guesses one."""
    items = plan.get("items") or []
    cur = plan.get("currency", "USD")
    used, max_calls, _ = budget(project_dir)
    rows, total, calls, missing = [], 0.0, 0, []
    for i, it in enumerate(items, 1):
        count = int(it.get("count", 1))
        qty = float(it.get("quantity", 1))
        price = it.get("unit_price")
        if price is None:
            missing.append(it.get("endpoint", f"item {i}"))
            sub = None
        else:
            sub = count * qty * float(price)
            total += sub
        calls += count
        rows.append(
            f"| {i} | `{it.get('endpoint', '?')}` | {it.get('purpose', '')} | {count} | "
            f"{qty:g} {it.get('unit', 'call')} | {'' if price is None else f'{float(price):g}'} | "
            f"{'?' if sub is None else f'{sub:.2f}'} | {it.get('price_source', '')} |"
        )
    lines = [
        "# Rencana generasi fal.ai (menunggu persetujuan)",
        "",
        f"| # | Endpoint | Untuk | Panggilan | Jumlah | Harga/unit ({cur}) | Subtotal ({cur}) | Sumber harga |",
        "|---|---|---|---|---|---|---|---|",
        *rows,
        "",
        f"**Total perkiraan: {total:.2f} {cur}** untuk {calls} panggilan. Anggaran proyek: {used} dari {max_calls} panggilan sudah dipakai.",
    ]
    if missing:
        lines.append(f"Harga belum diisi untuk: {', '.join(missing)}. Buka halaman model fal dan isi sebelum meminta persetujuan.")
    if used + calls > max_calls:
        lines.append(f"Rencana ini melebihi batas ({used + calls} > {max_calls}). Kurangi panggilan atau minta izin menaikkan fal.max_calls.")
    summary = {"total": round(total, 4), "currency": cur, "calls": calls, "calls_used": used, "max_calls": max_calls,
               "missing_prices": missing, "over_budget": used + calls > max_calls}
    return "\n".join(lines) + "\n", summary
