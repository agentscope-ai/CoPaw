#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
concat-clips.py — concatenate MP4 clips with a crossfade between adjacent
clips so cuts don't pop.

Usage:
    uv run tools/concat-clips.py --out final.mp4 \\
        --fade 0.6 \\
        clip1.mp4 clip2.mp4 [clip3.mp4 ...]

Notes
-----
We always re-encode (libx264) because crossfades require it. Audio is
crossfaded too (acrossfade) so the title music tails into the demo
narration smoothly.

For demos with N clips this produces N-1 transitions.
"""
from __future__ import annotations
import argparse, shlex, subprocess, sys, json
from pathlib import Path


def probe(path: Path) -> dict:
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=codec_type",
        "-of", "json", str(path),
    ]).decode()
    return json.loads(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--fade", type=float, default=0.6, help="Crossfade duration in seconds.")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("clips", nargs="+")
    args = ap.parse_args()

    clips = [Path(p).resolve() for p in args.clips]
    for c in clips:
        if not c.is_file():
            sys.exit(f"missing: {c}")
    durations = [float(probe(c)["format"]["duration"]) for c in clips]
    print("clip durations:", durations)

    fade = args.fade
    # Build a filter graph that chains xfade/acrossfade across clips.
    # xfade requires the offset to be in the FIRST stream's timeline — for
    # chained xfades we keep accumulating offsets relative to the running
    # output's duration: out_dur_after_i = out_dur_after_{i-1} + dur_i - fade.
    inputs: list[str] = []
    for c in clips:
        inputs += ["-i", str(c)]

    if len(clips) == 1:
        # Single clip — just copy
        cmd = ["ffmpeg", "-y", *inputs, "-c", "copy", "-movflags", "+faststart", args.out]
        print(">>", " ".join(shlex.quote(c) for c in cmd))
        subprocess.run(cmd, check=True)
        return

    filt: list[str] = []
    v_prev = "[0:v]"
    a_prev = "[0:a]"
    running = durations[0]
    for i in range(1, len(clips)):
        v_next = f"[{i}:v]"
        a_next = f"[{i}:a]"
        offset = running - fade
        v_out = f"[v{i}]"
        a_out = f"[a{i}]"
        filt.append(f"{v_prev}{v_next}xfade=transition=fade:duration={fade}:offset={offset}{v_out}")
        filt.append(f"{a_prev}{a_next}acrossfade=d={fade}{a_out}")
        v_prev, a_prev = v_out, a_out
        running = running + durations[i] - fade
    filter_complex = ";".join(filt)

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", v_prev, "-map", a_prev,
        "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        args.out,
    ]
    print(">>", " ".join(shlex.quote(c) for c in cmd))
    subprocess.run(cmd, check=True)
    print(f"wrote {args.out} (total ~{running:.1f}s)")


if __name__ == "__main__":
    main()
