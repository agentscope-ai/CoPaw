#!/usr/bin/env python3
"""Transcribe audio with word-level timestamps via OpenAI Whisper.

For every .mp3 in --audio-dir, calls the OpenAI audio transcription API
(default model: whisper-1) and writes {basename}.json beside it with
`words`, `segments`, `text`, and `duration` fields.

The OpenAI API key is read from the OPENAI_API_KEY environment variable
or from the .env file pointed to by --env (default: ./.env).

    python3 transcribe.py --audio-dir ./audio
    python3 transcribe.py --only diego,lin
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def load_env(path: Path) -> dict:
    env = {}
    if not path or not path.exists():
        return env
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def find_api_key(env_path: Path) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    env = load_env(env_path)
    if env.get("OPENAI_API_KEY"):
        return env["OPENAI_API_KEY"]
    sys.exit("OPENAI_API_KEY not found (checked env and {})".format(env_path))


def build_multipart(fields, files):
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        )
        parts.append(f"{v}\r\n".encode())
    for k, (fname, fdata, ctype) in files.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{k}"; filename="{fname}"\r\n'.encode()
        )
        parts.append(f"Content-Type: {ctype}\r\n\r\n".encode())
        parts.append(fdata)
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), boundary


def transcribe(audio_path: Path, api_key: str, model: str) -> dict:
    audio = audio_path.read_bytes()
    fields = {
        "model": model,
        "response_format": "verbose_json",
        "timestamp_granularities[]": "word",
    }
    files = {"file": (audio_path.name, audio, "audio/mpeg")}
    body, boundary = build_multipart(fields, files)
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        method="POST",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(
            f"Transcribe error {e.code} for {audio_path.name}:\n"
            f"{e.read().decode(errors='replace')}"
        )


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--audio-dir", type=Path, default=Path("audio"),
                   help="Directory of .mp3 files to transcribe (default: ./audio)")
    p.add_argument("--model", default="whisper-1",
                   help="Transcription model (default: whisper-1)")
    p.add_argument("--env", type=Path, default=Path(".env"),
                   help="Path to .env file (default: ./.env)")
    p.add_argument("--only", default=None,
                   help="Comma-separated scene names to (re)transcribe")
    args = p.parse_args()

    if not args.audio_dir.exists():
        sys.exit(f"Audio directory not found: {args.audio_dir}")

    api_key = find_api_key(args.env)

    audios = sorted(args.audio_dir.glob("*.mp3"))
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        audios = [a for a in audios if a.stem in wanted]
    if not audios:
        sys.exit(f"No matching .mp3 files in {args.audio_dir}")

    print(f"Model: {args.model}")
    print(f"Audio: {args.audio_dir} ({len(audios)} files)\n")

    for mp3 in audios:
        out = mp3.with_suffix(".json")
        print(f"  ▶ {mp3.name}", flush=True)
        data = transcribe(mp3, api_key, args.model)
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        n_words = len(data.get("words", []))
        dur = data.get("duration", 0.0)
        print(f"    ✓ {n_words} words · {dur:.2f}s → {out.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
