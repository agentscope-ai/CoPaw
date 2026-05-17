#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
record-html-movie.py — record an HTML "movie demo" to MP4.

Pipeline:
  1. Launch Chrome via the Node helper (puppeteer + CDP screencast).
  2. Capture JPEG frames + per-frame timestamps + scene/audio marks.
  3. Build an ffmpeg concat list of (frame, duration) and encode video.
  4. Build the audio track from per-scene mp3s anchored at the captured
     audio-play marks, padded with silence to match the video duration.
  5. Mux video + audio into the output mp4.

Why this works for our demo
---------------------------
The HTML's GSAP timeline is driven by `audio.currentTime` (audio is the
master clock), so the captured visuals are pinned to each scene's audio
in real time. As long as we mix the same per-scene mp3 files into the
final track at the moments the browser actually started playing them,
the result is frame-accurate.

Usage:
    uv run tools/record-html-movie.py \\
        --demo qwenpaw-agent-os-demo.html \\
        --out  qwenpaw-agent-os-demo.mp4 \\
        --width 1920 --height 1080 --fps 30

For another demo, pass --no-audio to skip audio assembly entirely (the
recorder still mutes browser audio so capture is silent — the resulting
mp4 will have no audio track unless you provide assets).
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print(">>", " ".join(shlex.quote(c) for c in cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--demo", help="Path to the HTML demo (relative to repo). Appends ?clean=1.")
    src.add_argument("--url",  help="Full URL to load (no auto-suffix).")
    ap.add_argument("--out",  required=True, help="Output mp4 path.")
    ap.add_argument("--width",  type=int, default=1920, help="Logical viewport width.")
    ap.add_argument("--height", type=int, default=1080, help="Logical viewport height.")
    ap.add_argument("--dpr",    type=float, default=1.0,
                    help="deviceScaleFactor — capture at viewport*DPR pixels for supersampling.")
    ap.add_argument("--out-width",  type=int, default=None, help="Final video width (defaults to viewport width).")
    ap.add_argument("--out-height", type=int, default=None, help="Final video height (defaults to viewport height).")
    ap.add_argument("--fps",    type=int, default=30, help="Output frame rate.")
    ap.add_argument("--quality", type=int, default=90, help="Screencast JPEG quality.")
    ap.add_argument("--crf", type=int, default=18, help="libx264 CRF (lower = higher quality).")
    ap.add_argument("--preset", default="medium", help="libx264 preset (medium/slow/slower).")
    ap.add_argument("--audio-dir", default="assets/audio",
                    help="Directory containing per-scene mp3s named like why-field.mp3, mia.mp3, etc.")
    ap.add_argument("--audio-track", default=None,
                    help="Pre-built audio file to mux as-is (bypasses scene-based assembly).")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--keep-frames", action="store_true",
                    help="Keep the intermediate frames directory (for debugging).")
    ap.add_argument("--frames-dir", default=None,
                    help="Reuse a pre-recorded frames directory (skips browser capture).")
    ap.add_argument("--max-secs", type=int, default=1500,
                    help="Hard ceiling on capture duration.")
    args = ap.parse_args()

    if args.demo:
        demo_path = (REPO / args.demo).resolve()
        if not demo_path.is_file():
            sys.exit(f"demo not found: {demo_path}")
        url = f"file://{demo_path}?clean=1"
    else:
        url = args.url
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    work = Path(args.frames_dir) if args.frames_dir else Path(tempfile.mkdtemp(prefix="moviecap_"))
    frames_dir = work / "frames"
    marks_path = work / "marks.json"
    print(f"work dir: {work}")

    if args.frames_dir:
        # Reusing prior capture
        if not frames_dir.is_dir():
            sys.exit(f"--frames-dir given but {frames_dir} missing")
    else:
        frames_dir.mkdir(exist_ok=True)
        cmd = [
            "node", str(REPO / "tools" / "record-html-movie.js"),
            "--url", url,
            "--frames", str(frames_dir),
            "--marks",  str(marks_path),
            "--width",  str(args.width),
            "--height", str(args.height),
            "--dpr",    str(args.dpr),
            "--quality", str(args.quality),
            "--max-secs", str(args.max_secs),
        ]
        run(cmd, cwd=REPO)

    marks = json.loads(marks_path.read_text())
    n_frames = marks["frameCount"]
    duration = marks["endedAt"]
    print(f"frames: {n_frames}, duration: {duration:.2f}s")

    # ────────── build concat list with per-frame durations ──────────
    # ffmpeg concat demuxer format:
    #   file 'frame_path'
    #   duration <seconds-this-frame-shown>
    # The last entry needs the file path repeated (ffmpeg quirk).
    frame_ts: list[tuple[Path, float]] = []
    for i in range(1, n_frames + 1):
        name = f"{i:06d}"
        jpg = frames_dir / f"{name}.jpg"
        t   = float((frames_dir / f"{name}.t").read_text().strip())
        frame_ts.append((jpg, t))
    # convert absolute timestamps -> durations
    durations: list[float] = []
    for i in range(len(frame_ts) - 1):
        d = frame_ts[i + 1][1] - frame_ts[i][1]
        durations.append(max(0.005, d))
    if frame_ts:
        durations.append(max(0.005, duration - frame_ts[-1][1]))

    concat_txt = work / "concat.txt"
    with concat_txt.open("w") as f:
        for (jpg, _), d in zip(frame_ts, durations):
            f.write(f"file '{jpg.as_posix()}'\nduration {d:.5f}\n")
        # ffmpeg demuxer quirk: repeat the last file
        if frame_ts:
            f.write(f"file '{frame_ts[-1][0].as_posix()}'\n")

    video_only = work / "video.mp4"
    # Compose the video filter chain:
    #   fps=N                       — fixed output rate from variable capture
    #   scale=...:flags=lanczos     — supersample down (only if captured > out)
    #   format=yuv420p              — broad player compat
    out_w = args.out_width  or args.width
    out_h = args.out_height or args.height
    cap_w = round(args.width  * args.dpr)
    cap_h = round(args.height * args.dpr)
    vf_parts = [f"fps={args.fps}"]
    if (cap_w, cap_h) != (out_w, out_h):
        vf_parts.append(f"scale={out_w}:{out_h}:flags=lanczos")
    vf_parts.append("format=yuv420p")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-vf", ",".join(vf_parts),
        "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
        "-movflags", "+faststart",
        str(video_only),
    ])

    # ────────── audio track ──────────
    if args.no_audio:
        shutil.copy2(video_only, out_path)
        print(f"wrote {out_path} (no audio)")
    elif args.audio_track:
        # Pre-built audio: mux as-is, trimmed/padded to the video duration.
        audio_only = work / "audio.m4a"
        run([
            "ffmpeg", "-y", "-i", str((REPO / args.audio_track).resolve()),
            "-af", f"apad,atrim=duration={duration:.3f},aformat=channel_layouts=stereo:sample_rates=48000",
            "-c:a", "aac", "-b:a", "192k", str(audio_only),
        ])
        run([
            "ffmpeg", "-y", "-i", str(video_only), "-i", str(audio_only),
            "-c:v", "copy", "-c:a", "copy",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", "-movflags", "+faststart",
            str(out_path),
        ])
        print(f"wrote {out_path}")
    else:
        audio_dir = (REPO / args.audio_dir).resolve()
        # Each "audio-play" mark = an audio for that scene started at time t.
        # Note: t is browser wall-clock relative to recorder t0, which matches
        # the frame timestamps. Build a track with anull + amix layering.
        audio_marks = [m for m in marks["marks"] if m.get("kind") == "audio-play"]
        if not audio_marks:
            print("no audio-play marks captured — falling back to video-only")
            shutil.copy2(video_only, out_path)
            return

        # Build an audio track using -filter_complex: pad each scene's mp3
        # with `adelay=ms|ms` and amix them all together. Layering is fine
        # because the scenes don't overlap (audio.onended drives the chain).
        inputs: list[str] = []
        filt_parts: list[str] = []
        amix_in: list[str] = []
        for i, m in enumerate(audio_marks):
            scene = m["scene"]
            mp3 = audio_dir / f"{scene}.mp3"
            if not mp3.is_file():
                print(f"  skip {scene}: {mp3} missing")
                continue
            delay_ms = int(round(m["t"] * 1000))
            inputs += ["-i", str(mp3)]
            label_in  = f"[{len(amix_in)}:a]"
            label_out = f"[a{i}]"
            # adelay needs per-channel delays "ms|ms"; aformat ensures stereo.
            filt_parts.append(
                f"{label_in}aformat=channel_layouts=stereo:sample_rates=48000,"
                f"adelay={delay_ms}|{delay_ms}{label_out}"
            )
            amix_in.append(label_out)
        if not amix_in:
            print("no usable mp3s — writing video-only")
            shutil.copy2(video_only, out_path)
            return

        # Mix them and cap the duration to the video's duration.
        filter_complex = ";".join(filt_parts) + ";" + "".join(amix_in) + \
            f"amix=inputs={len(amix_in)}:duration=longest:normalize=0,apad,atrim=duration={duration:.3f}[aout]"

        audio_only = work / "audio.m4a"
        run([
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", "[aout]",
            "-c:a", "aac", "-b:a", "192k",
            str(audio_only),
        ])

        run([
            "ffmpeg", "-y", "-i", str(video_only), "-i", str(audio_only),
            "-c:v", "copy", "-c:a", "copy",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", "-movflags", "+faststart",
            str(out_path),
        ])
        print(f"wrote {out_path}")

    if not args.keep_frames and not args.frames_dir:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
