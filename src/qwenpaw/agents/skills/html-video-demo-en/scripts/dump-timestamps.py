#!/usr/bin/env python3
"""Pretty-print phrase-level transcripts from Whisper JSON output.

Reads every .json transcript in --audio-dir and prints lines grouped by
punctuation or pause, with start-end timestamps. Useful for picking
anchor times when authoring scene checkpoints.

    python3 dump-timestamps.py --audio-dir ./audio
    python3 dump-timestamps.py --audio-dir ./audio --only diego,lin
"""

import argparse
import json
from pathlib import Path


def chunks(words, pause_threshold=0.5):
    """Group words into sentence-like chunks by punctuation or pause."""
    line = []
    start = 0.0
    for i, w in enumerate(words):
        if not line:
            start = w["start"]
        line.append(w["word"])
        text = " ".join(line)
        is_end = i == len(words) - 1
        is_punct = text.rstrip().endswith((".", "?", "—", "...", ":", ","))
        is_pause = (
            i + 1 < len(words)
            and (words[i + 1]["start"] - w["end"]) > pause_threshold
        )
        if is_punct or is_end or is_pause:
            yield (start, w["end"], text)
            line = []


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--audio-dir", type=Path, default=Path("audio"),
                   help="Directory containing .json transcripts (default: ./audio)")
    p.add_argument("--pause-threshold", type=float, default=0.5,
                   help="Gap in seconds that splits one chunk from the next (default: 0.5)")
    p.add_argument("--only", default=None,
                   help="Comma-separated scene names to print")
    args = p.parse_args()

    jsons = sorted(args.audio_dir.glob("*.json"))
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        jsons = [j for j in jsons if j.stem in wanted]

    for j in jsons:
        data = json.loads(j.read_text())
        dur = data.get("duration", 0.0)
        print(f"\n══════ {j.stem} ({dur:.2f}s) ══════")
        for start, end, text in chunks(data.get("words", []),
                                       pause_threshold=args.pause_threshold):
            print(f"  {start:5.2f}-{end:5.2f}  {text}")


if __name__ == "__main__":
    main()
