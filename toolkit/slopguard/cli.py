"""slopguard command line.

Exit codes: 0 clean, 1 FLOOR failure, 2 open REFLEX findings, 3 usage/setup error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from slopguard import __version__, build, captions, fal, ledger, media, project, sheet, textlint, videoqa
from slopguard.report import EXIT_USAGE, Report, apply_waivers, load_waivers, write_outputs


def _print(report: Report, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(report.to_markdown())


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def cmd_init(a) -> int:
    written = project.init_project(a.path, a.title or os.path.basename(os.path.abspath(a.path)), a.format, a.duration, a.lang, a.max_calls)
    for w in written:
        print(f"created {w}")
    if not written:
        print("nothing created (all files already exist)")
    return 0


def cmd_lint_script(a) -> int:
    cfg = project.load_config(a.file)
    extra = (cfg.get("lexicon") or {}).get("extra") or []
    duration = a.duration or cfg.get("duration")
    lang = a.lang if a.lang != "auto" else cfg.get("lang", "auto")
    report = textlint.lint_script(_read(a.file), lang=lang, target_seconds=duration, subject=a.file, extra_lexicon=extra)
    waivers = load_waivers(a.waivers or (os.path.join(cfg["_root"], "waivers.json") if cfg else None))
    apply_waivers(report, waivers)
    write_outputs(report, a.out, "script-lint")
    _print(report, a.json)
    return report.exit_code()


def cmd_captions(a) -> int:
    duration = media.probe(a.video).duration if a.video else None
    report = captions.check_captions(_read(a.file), subject=a.file, video_duration=duration, max_cps=a.max_cps, max_chars=a.max_chars)
    write_outputs(report, a.out, "captions")
    _print(report, a.json)
    return report.exit_code()


def cmd_ledger(a) -> int:
    report = ledger.check_ledger(_read(a.file), subject=a.file, max_generated_share=a.max_generated)
    cfg = project.load_config(a.file)
    apply_waivers(report, load_waivers(a.waivers or (os.path.join(cfg["_root"], "waivers.json") if cfg else None)))
    write_outputs(report, a.out, "ledger")
    _print(report, a.json)
    return report.exit_code()


def cmd_qa(a) -> int:
    cfg = project.load_config(a.video)
    root = cfg.get("_root")
    target = a.target or cfg.get("target")
    duration = a.duration if a.duration is not None else cfg.get("duration")
    lufs = a.lufs if a.lufs is not None else cfg.get("lufs", -14.0)
    try:
        report, probe, pic = videoqa.qa_video(
            a.video,
            target=target,
            target_duration=duration,
            lufs_target=float(lufs),
            silent_ok=a.silent_ok,
            freeze_max=a.freeze_max,
            scene_threshold=a.scene,
            full_frame=a.full_frame,
        )
    except media.MediaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    caps = a.captions
    if caps:
        cr = captions.check_captions(_read(caps), subject=caps, video_duration=probe.duration if probe else None)
        report.extend(cr.findings)
        report.metrics.update({f"captions: {k}": v for k, v in cr.metrics.items()})
        report.manual_checks += cr.manual_checks
    led = a.ledger or (os.path.join(root, "ledger.csv") if root and os.path.exists(os.path.join(root, "ledger.csv")) else None)
    if led:
        lr = ledger.check_ledger(_read(led), subject=led)
        if lr.metrics.get("shots"):
            report.extend(lr.findings)
            report.metrics.update({f"ledger: {k}": v for k, v in lr.metrics.items()})
    waivers_path = a.waivers or (os.path.join(root, "waivers.json") if root else None)
    apply_waivers(report, load_waivers(waivers_path))
    out = a.out or (os.path.join(root, "edit", "qa") if root else os.path.splitext(a.video)[0] + ".qa")
    if not a.no_sheets and probe and pic is not None:
        ov = sheet.overview(a.video, out, duration=probe.duration)
        cs = sheet.cut_strip(a.video, [c for c in pic.cuts if 0.2 < c < probe.duration - 0.2], out)
        report.metrics["contact sheets"] = ", ".join(p for p in (ov, cs) if p) or "none"
    paths = write_outputs(report, out, "qa-report")
    _print(report, a.json)
    if paths and not a.json:
        print(f"wrote {', '.join(paths)}")
    return report.exit_code()


def cmd_sheet(a) -> int:
    p = media.probe(a.video)
    ov = sheet.overview(a.video, a.out, count=a.count, duration=p.duration)
    print(ov or "no frames extracted")
    if a.cuts:
        pic = media.picture_stats(a.video, p.duration)
        cs = sheet.cut_strip(a.video, [c for c in pic.cuts if 0.2 < c < p.duration - 0.2], a.out)
        print(cs or "no cuts detected")
    return 0


def cmd_fal(a) -> int:
    try:
        if a.fal_cmd == "budget":
            used, mx, log = fal.budget(a.project)
            print(json.dumps({"calls_used": used, "max_calls": mx, "log": log}))
            return 0
        if a.fal_cmd == "upload":
            print(fal.upload_file(a.file))
            return 0
        if a.fal_cmd == "result":
            print(json.dumps(fal._json("GET", a.response_url), indent=2))
            return 0
        if a.fal_cmd == "run":
            payload = {}
            base_dir = os.getcwd()
            if a.input:
                payload = json.loads(_read(a.input))
                base_dir = os.path.dirname(os.path.abspath(a.input))
            for kv in a.arg or []:
                k, _, v = kv.partition("=")
                try:
                    payload[k] = json.loads(v)
                except json.JSONDecodeError:
                    payload[k] = v
            res = fal.run(
                a.endpoint,
                payload,
                out_dir=a.out,
                project_dir=a.project,
                confirm=a.confirm,
                max_wait=a.max_wait,
                label=a.label or "",
                on_status=lambda s, _: print(f"status: {s}", file=sys.stderr),
                base_dir=base_dir,
            )
            print(json.dumps({"request_id": res["request_id"], "files": res["files"]}, indent=2))
            return 0
    except fal.FalError as exc:
        print(f"fal error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    return EXIT_USAGE


def cmd_build_captions(a) -> int:
    words = build.extract_words(json.loads(_read(a.words)))
    if not words:
        print("error: no word timings found in the transcript JSON", file=sys.stderr)
        return EXIT_USAGE
    if a.edl:
        edl = json.loads(_read(a.edl))
        words = build.map_to_output(words, edl.get("ranges", edl if isinstance(edl, list) else []))
    cfg = project.load_config(a.out)
    lang = a.lang or cfg.get("lang", "id")
    video_end = media.probe(a.video).duration if a.video else None
    cues = build.captions_from_words(words, lang=lang, max_chars=a.max_chars, max_cps=a.max_cps, video_end=video_end)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(build.to_srt(cues))
    report = captions.check_captions(_read(a.out), subject=a.out, video_duration=video_end)
    print(f"wrote {a.out}: {len(cues)} cues from {len(words)} words; {report.verdict()}")
    return report.exit_code()


def cmd_master(a) -> int:
    cfg = project.load_config(a.input)
    lufs = a.lufs if a.lufs is not None else cfg.get("lufs", -14.0)
    res = build.master_loudness(a.input, a.out, lufs=float(lufs), tp=a.tp)
    print(json.dumps(res, indent=2))
    ok = res["after_lufs"] is not None and abs(res["after_lufs"] - float(lufs)) <= 1.0 and (res["after_true_peak"] or 0) <= -1.0
    return 0 if ok else 2


def cmd_doctor(a) -> int:
    ok = True
    ff = media._find("ffmpeg")
    fp = media.ffprobe_path()
    print(f"slopguard {__version__}  python {sys.version.split()[0]}")
    print(f"ffmpeg : {ff or 'MISSING (run toolkit/setup.sh)'}")
    print(f"ffprobe: {fp or 'not found (optional; ffmpeg -i parsing is used)'}")
    print(f"FAL_KEY: {'set' if os.environ.get('FAL_KEY') else 'not set (needed only for fal generation)'}")
    if not ff:
        ok = False
    else:
        code, out, err = media.run([ff, "-hide_banner", "-filters"], timeout=60)
        need = ["ebur128", "silencedetect", "blackdetect", "freezedetect", "signalstats", "showinfo", "tile", "loudnorm"]
        missing = [n for n in need if f" {n} " not in out]
        print(f"filters: {'all present' if not missing else 'MISSING ' + ', '.join(missing)}")
        ok = ok and not missing
    return 0 if ok else EXIT_USAGE


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="slopguard", description="Anti-slop quality gates for AI-assisted video.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="scaffold a video project folder")
    s.add_argument("path")
    s.add_argument("--title")
    s.add_argument("--format", default="vertical", choices=sorted(project.FORMATS))
    s.add_argument("--duration", type=int, default=45)
    s.add_argument("--lang", default="id")
    s.add_argument("--max-calls", type=int, default=12, help="fal.ai call budget for this project")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("lint-script", help="lint narration for slop, unsourced claims, pacing")
    s.add_argument("file")
    s.add_argument("--lang", default="auto", choices=["auto", "en", "id"])
    s.add_argument("--duration", type=float, help="target video length in seconds")
    s.add_argument("--waivers")
    s.add_argument("--out")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_lint_script)

    s = sub.add_parser("check-captions", help="check SRT/VTT readability and timing")
    s.add_argument("file")
    s.add_argument("--video", help="rendered video, to check cues against its duration")
    s.add_argument("--max-cps", type=float, default=20.0)
    s.add_argument("--max-chars", type=int, default=42)
    s.add_argument("--out")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_captions)

    s = sub.add_parser("check-ledger", help="check the shot ledger (sources, licenses, ideas)")
    s.add_argument("file")
    s.add_argument("--max-generated", type=float, default=0.6, help="max share of runtime that may be generated")
    s.add_argument("--waivers")
    s.add_argument("--out")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_ledger)

    s = sub.add_parser("qa", help="measure a rendered video (+captions, +ledger) and write a report")
    s.add_argument("video")
    s.add_argument("--target", help="WxH or vertical|landscape|square|portrait45|4k")
    s.add_argument("--duration", type=float)
    s.add_argument("--lufs", type=float)
    s.add_argument("--captions")
    s.add_argument("--ledger")
    s.add_argument("--waivers")
    s.add_argument("--silent-ok", action="store_true")
    s.add_argument("--freeze-max", type=float, default=2.5)
    s.add_argument("--scene", type=float, default=0.30, help="scene-change threshold for cut detection")
    s.add_argument("--full-frame", action="store_true", help="do not exclude caption band/platform UI from freeze detection")
    s.add_argument("--no-sheets", action="store_true")
    s.add_argument("--out")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_qa)

    s = sub.add_parser("sheet", help="contact sheet (+ cut strip) for visual review")
    s.add_argument("video")
    s.add_argument("--out", default="edit/qa")
    s.add_argument("--count", type=int, default=20)
    s.add_argument("--cuts", action="store_true")
    s.set_defaults(func=cmd_sheet)

    s = sub.add_parser("fal", help="fal.ai generation with a spending guard")
    fs = s.add_subparsers(dest="fal_cmd", required=True)
    r = fs.add_parser("run", help="submit, wait, download outputs")
    r.add_argument("endpoint", help="e.g. fal-ai/nano-banana-pro")
    r.add_argument("--input", help="JSON file with the model input")
    r.add_argument("--arg", action="append", help="key=value (value parsed as JSON when possible)")
    r.add_argument("--out", default="gen")
    r.add_argument("--project", default=".")
    r.add_argument("--label")
    r.add_argument("--max-wait", type=int, default=900)
    r.add_argument("--confirm", action="store_true", help="required: the user approved this paid call")
    u = fs.add_parser("upload", help="upload a local file, print its URL")
    u.add_argument("file")
    rs = fs.add_parser("result", help="fetch a finished result by response URL")
    rs.add_argument("--response-url", required=True)
    b = fs.add_parser("budget", help="show calls used / allowed")
    b.add_argument("--project", default=".")
    s.set_defaults(func=cmd_fal)

    s = sub.add_parser("captions", help="build a readable SRT from word timestamps (Scribe/Whisper/fal JSON)")
    s.add_argument("words", help="transcript JSON with word-level timings")
    s.add_argument("--out", required=True, help="output .srt")
    s.add_argument("--edl", help="EDL JSON with ranges[{start,end}] to map source time to output time")
    s.add_argument("--video", help="rendered video, to clamp cues to its end")
    s.add_argument("--lang", choices=["id", "en"])
    s.add_argument("--max-chars", type=int, default=42)
    s.add_argument("--max-cps", type=float, default=17.0)
    s.set_defaults(func=cmd_build_captions)

    s = sub.add_parser("master", help="two-pass loudness master (video stream copied)")
    s.add_argument("input")
    s.add_argument("--out", required=True)
    s.add_argument("--lufs", type=float)
    s.add_argument("--tp", type=float, default=-1.5)
    s.set_defaults(func=cmd_master)

    s = sub.add_parser("doctor", help="check ffmpeg, filters and FAL_KEY presence")
    s.set_defaults(func=cmd_doctor)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except media.MediaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
