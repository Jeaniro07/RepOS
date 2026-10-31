"""Rendered-video gates. Measures; never claims a video is good.

Thresholds come from production practice gathered in the reference repos
(browser-use/video-use, heygen-com/hyperframes, kaomei/stickman-video-director,
Vincentwei1021/video-shotcraft) and platform loudness norms:
  - no principal-picture inactivity > 2.5 s (stickman-video-director)
  - more than 3 s with nothing changing is a dead stretch (hyperframes)
  - an empty first frame is an empty thumbnail (hyperframes)
  - a film over ~15 s with no sound is silent by mistake (hyperframes)
  - mix to about -14 LUFS, true peak <= -1 dBTP (video-use)
"""

from __future__ import annotations

import statistics
from typing import List, Optional, Tuple

from slopguard import media
from slopguard.report import FINISH, FLOOR, REFLEX, Finding, Report

PRESETS = {
    "vertical": (1080, 1920),
    "landscape": (1920, 1080),
    "square": (1080, 1080),
    "portrait45": (1080, 1350),
    "4k": (3840, 2160),
}


def parse_target(value: Optional[str]) -> Optional[Tuple[int, int]]:
    if not value:
        return None
    if value in PRESETS:
        return PRESETS[value]
    if "x" in value:
        w, h = value.lower().split("x", 1)
        return int(w), int(h)
    raise ValueError(f"Unknown target '{value}'. Use WxH or one of: {', '.join(PRESETS)}")


def qa_video(
    path: str,
    target: Optional[str] = None,
    target_duration: Optional[float] = None,
    lufs_target: float = -14.0,
    lufs_tolerance: float = 2.0,
    silent_ok: bool = False,
    freeze_max: float = 2.5,
    dead_air: float = 1.5,
    scene_threshold: float = 0.30,
    full_frame: bool = False,
) -> Tuple[Report, Optional[media.Probe], Optional[media.PictureStats]]:
    report = Report(subject=path, kind="video")
    try:
        p = media.probe(path)
    except media.MediaError as exc:
        report.add(Finding("video.decode", FLOOR, str(exc), fix="Re-render; the file must decode."))
        return report, None, None

    if not p.has_video or p.duration <= 0:
        report.add(Finding("video.decode", FLOOR, "No decodable video stream.", fix="Re-render."))
        return report, p, None

    w, h = p.display_size
    report.metrics["size"] = f"{w}x{h}"
    report.metrics["duration (s)"] = round(p.duration, 2)
    report.metrics["fps"] = round(p.fps, 3)
    report.metrics["video codec"] = p.vcodec
    report.metrics["audio"] = f"{p.acodec} {p.sample_rate} Hz" if p.has_audio else "none"

    # -- format
    tgt = parse_target(target)
    if tgt:
        if (w, h) != tgt:
            same_aspect = abs(w / h - tgt[0] / tgt[1]) < 0.01
            report.add(
                Finding(
                    "video.size",
                    REFLEX if same_aspect else FLOOR,
                    f"Rendered {w}x{h}, target {tgt[0]}x{tgt[1]}"
                    + (" (same aspect, different resolution)." if same_aspect else " (wrong aspect ratio)."),
                    fix="Render at the delivery size; never letterbox a vertical video into landscape or the reverse.",
                )
            )
    if min(w, h) < 720:
        report.add(Finding("video.low-res", REFLEX, f"Short side is {min(w, h)} px.", fix="Deliver at least 1080 on the short side."))
    if p.fps and p.fps < 23.5:
        report.add(Finding("video.fps", REFLEX, f"{p.fps:.2f} fps reads as choppy.", fix="Render at 24, 25 or 30 fps."))
    if target_duration:
        report.metrics["target duration (s)"] = target_duration
        if abs(p.duration - target_duration) > max(1.0, 0.10 * target_duration):
            report.add(
                Finding(
                    "video.duration",
                    REFLEX,
                    f"{p.duration:.1f}s against a {target_duration:.0f}s target.",
                    fix="Recut to the brief, or update the brief on purpose.",
                )
            )
    if p.bitrate and w and h and p.fps:
        bpp = p.bitrate / (w * h * p.fps)
        report.metrics["bits per pixel"] = round(bpp, 3)
        if bpp < 0.04:
            report.add(
                Finding(
                    "encode.bitrate",
                    FINISH,
                    f"{p.bitrate / 1e6:.1f} Mb/s is thin for {w}x{h}@{p.fps:.0f}; expect banding/blocks after platform re-encode.",
                    fix="Encode H.264 CRF 18-20 (or 12+ Mb/s at 1080p).",
                )
            )

    # -- sound
    if not p.has_audio:
        if p.duration > 15 and not silent_ok:
            report.add(
                Finding(
                    "audio.missing",
                    FLOOR,
                    f"{p.duration:.0f}s video with no audio track.",
                    fix="Add narration/music/sound on visible actions, or pass --silent-ok if silence is the brief.",
                )
            )
    else:
        a = media.audio_stats(path, silence_min=dead_air)
        report.metrics["integrated loudness (LUFS)"] = a.integrated_lufs if a.integrated_lufs is not None else "silent"
        report.metrics["true peak (dBTP)"] = a.true_peak_dbtp if a.true_peak_dbtp is not None else "n/a"
        if a.loudness_range is not None:
            report.metrics["loudness range (LU)"] = a.loudness_range
        if a.integrated_lufs is None:
            if not silent_ok and p.duration > 15:
                report.add(Finding("audio.silent", FLOOR, "Audio track is digital silence.", fix="Mix the audio in, or drop the track and pass --silent-ok."))
        else:
            if abs(a.integrated_lufs - lufs_target) > lufs_tolerance:
                report.add(
                    Finding(
                        "audio.loudness",
                        REFLEX,
                        f"Integrated {a.integrated_lufs:.1f} LUFS, target {lufs_target:.0f} ±{lufs_tolerance:.0f}.",
                        fix=f"Two-pass loudnorm on the final mix: loudnorm=I={lufs_target:.0f}:TP=-1:LRA=11.",
                    )
                )
        if a.true_peak_dbtp is not None:
            if a.true_peak_dbtp > -0.3:
                report.add(
                    Finding(
                        "audio.clipping",
                        FLOOR,
                        f"True peak {a.true_peak_dbtp:.1f} dBTP; it will clip after platform encoding.",
                        fix="Limit to -1 dBTP on the master.",
                    )
                )
            elif a.true_peak_dbtp > -1.0:
                report.add(Finding("audio.true-peak", REFLEX, f"True peak {a.true_peak_dbtp:.1f} dBTP (want <= -1).", fix="Limit to -1 dBTP."))
        dead = [(s, e if e >= 0 else p.duration) for s, e in a.silences]
        dead = [(s, e) for s, e in dead if s > 0.5 and e < p.duration - 0.5 and e - s >= dead_air]
        for s, e in dead:
            report.add(
                Finding(
                    "audio.dead-air",
                    REFLEX,
                    f"{e - s:.1f}s of silence mid-video.",
                    at=f"{s:.2f}s",
                    fix="Tighten the cut, or carry it with room tone/music if the pause is meant.",
                )
            )
        report.metrics["dead-air gaps"] = len(dead)

    # -- picture
    pic = media.picture_stats(
        path, p.duration, scene_threshold=scene_threshold, freeze_min=freeze_max, principal_region=not full_frame
    )
    for s, e in pic.blacks:
        at_edge = s < 0.15 or e > p.duration - 0.15
        if at_edge and e - s < 1.0:
            continue  # fade in/out
        report.add(
            Finding(
                "picture.black",
                FLOOR if e - s >= 2.0 and not at_edge else REFLEX,
                f"{e - s:.1f}s of black.",
                at=f"{s:.2f}s",
                fix="A missing clip or a failed overlay; check the edit at this time.",
            )
        )
    freeze_total = 0.0
    for s, e in pic.freezes:
        dur = e - s
        freeze_total += dur
        report.add(
            Finding(
                "picture.frozen",
                REFLEX,
                f"Principal picture does not change for {dur:.1f}s (max {freeze_max:.1f}s).",
                at=f"{s:.2f}s",
                fix="Give the frame a meaningful event (a reveal, an action, a new shot). Subtitle turnover or a slow zoom does not count.",
            )
        )
    if p.duration > 0:
        share = freeze_total / p.duration
        report.metrics["frozen share of runtime"] = f"{share * 100:.0f}%"
        if share > 0.40 and p.duration > 10:
            report.add(
                Finding(
                    "edit.slideshow",
                    REFLEX,
                    f"{share * 100:.0f}% of the runtime is frozen picture: it reads as a slideshow.",
                    fix="Replace held stills with motion that explains the narration.",
                )
            )
    flicker = [seg for seg in media.flicker_segments(pic.luma) if seg[1] - seg[0] >= 0.5]
    report.metrics["flicker stretches"] = len(flicker)
    for fs, fe, rate in flicker:
        report.add(
            Finding(
                "picture.flicker",
                REFLEX,
                f"Brightness flips up/down on {rate * 100:.0f}% of frames for {fe - fs:.1f}s: temporal flicker, a generated-video tell.",
                at=f"{fs:.2f}s",
                fix="Regenerate or replace the clip. For mild flicker try ffmpeg -vf deflicker=size=5:mode=pm, then look again.",
            )
        )
    if pic.first_frame_luma is not None:
        report.metrics["first frame luma / range"] = f"{pic.first_frame_luma:.0f} / {pic.first_frame_range:.0f}"
        if pic.first_frame_luma < 18 or (pic.first_frame_range or 0) < 12:
            report.add(
                Finding(
                    "picture.first-frame",
                    REFLEX,
                    "First frame is black or flat; it becomes the thumbnail and the first impression.",
                    at="0.00s",
                    fix="Open on the hook image at frame 0 (no fade from black on social).",
                )
            )

    cuts = sorted(c for c in pic.cuts if 0.2 < c < p.duration - 0.2)
    report.metrics["cuts detected"] = len(cuts)
    if cuts:
        bounds = [0.0] + cuts + [p.duration]
        shots = [b - a for a, b in zip(bounds, bounds[1:]) if b - a > 0.05]
        if shots:
            mean = statistics.mean(shots)
            report.metrics["mean shot length (s)"] = round(mean, 2)
            if len(cuts) >= 6:
                cv = statistics.pstdev(shots) / mean if mean else 0
                report.metrics["shot length CV"] = round(cv, 2)
                if cv < 0.18:
                    report.add(
                        Finding(
                            "edit.metronomic",
                            REFLEX,
                            f"{len(cuts)} cuts at near-identical intervals (CV {cv:.2f}, ~{mean:.1f}s each): template pacing.",
                            fix="Cut on meaning (speech boundaries, actions, beats), not on a timer.",
                        )
                    )
    report.metrics["cut times (s)"] = [round(c, 2) for c in cuts[:40]]

    report.manual_checks += [
        "Watch it once at full speed on a phone-sized window; note the first moment you'd swipe away.",
        "Listen through headphones: voice intelligible over music, no pops at cuts, effects tied to visible events.",
        "Every on-screen object reads as what it is without a label; nothing important sits under platform UI.",
        "Realistic AI-generated people, places or events are disclosed on upload (platform 'altered or synthetic' label).",
        "Nothing shows a real person saying or doing something they did not say or do.",
    ]
    return report, p, pic


def cut_windows(cuts: List[float], duration: float, pad: float = 0.2) -> List[Tuple[float, float]]:
    return [(max(0.0, c - pad), min(duration, c + pad)) for c in cuts]
