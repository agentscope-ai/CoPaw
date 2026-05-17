#!/usr/bin/env python3
"""Generate per-scene narration audio from text scripts.

For every .txt file in --scripts-dir, calls a Text-to-Speech API and
writes {basename}.mp3 to --out-dir. Two backends are supported:

  openai   gpt-4o-mini-tts (default voices: ash/sage/verse/...)
  qwen     DashScope qwen3-tts-flash (default voices: Cherry/Ethan/...)

Backend selection:
  --backend auto (default) picks based on available API keys; if both
  OPENAI_API_KEY and DASHSCOPE_API_KEY are set, prompts interactively.
  --backend openai or --backend qwen forces a choice.

For Qwen, the regional endpoint must match the API key:
  --region cn    https://dashscope.aliyuncs.com           (China)
  --region intl  https://dashscope-intl.aliyuncs.com      (Singapore)
  --region us    https://dashscope-us.aliyuncs.com        (Virginia)
Keys from different regions are not interchangeable. The script honors
DASHSCOPE_REGION from the env (cn / intl / us) before falling back to
--region (default: cn).

Examples
--------
    python3 generate-tts.py --scripts-dir ./scripts --out-dir ./audio
    python3 generate-tts.py --backend qwen --voice Cherry
    python3 generate-tts.py --backend openai --voice sage --speed 0.95
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_INSTRUCTIONS = (
    "Calm, confident, professional product-demo narration. "
    "Measured pacing with natural pauses between sentences. "
    "Speak with clarity and warmth, like a thoughtful technical narrator."
)

# Default voices per backend. Both lists are illustrative — each API has
# more voices than this; pick the one that fits your demo's tone.
DEFAULT_VOICE = {"openai": "ash", "qwen": "Cherry"}
DEFAULT_MODEL = {"openai": "gpt-4o-mini-tts", "qwen": "qwen3-tts-flash"}

# DashScope endpoints (the path is the same; only the host changes).
QWEN_HOSTS = {
    "cn":   "https://dashscope.aliyuncs.com",
    "intl": "https://dashscope-intl.aliyuncs.com",
    "us":   "https://dashscope-us.aliyuncs.com",
}
QWEN_PATH = "/api/v1/services/aigc/multimodal-generation/generation"


# ────────────────────────── env / key handling ──────────────────────────


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


def resolve_key(name: str, env_file: dict) -> str | None:
    return os.environ.get(name) or env_file.get(name)


def pick_backend(want: str, env_file: dict) -> str:
    """Return 'openai' or 'qwen' based on --backend and available keys."""
    openai_ok = bool(resolve_key("OPENAI_API_KEY", env_file))
    qwen_ok   = bool(resolve_key("DASHSCOPE_API_KEY", env_file))
    if want == "openai":
        if not openai_ok:
            sys.exit("OPENAI_API_KEY not found (env or .env). "
                     "Set it or use --backend qwen.")
        return "openai"
    if want == "qwen":
        if not qwen_ok:
            sys.exit("DASHSCOPE_API_KEY not found (env or .env). "
                     "Set it or use --backend openai.")
        return "qwen"
    # auto
    if openai_ok and not qwen_ok:
        return "openai"
    if qwen_ok and not openai_ok:
        return "qwen"
    if not openai_ok and not qwen_ok:
        sys.exit("Neither OPENAI_API_KEY nor DASHSCOPE_API_KEY found. "
                 "Set one (or pass --backend explicitly and provide the key).")
    # Both keys present → prompt
    sys.stderr.write(
        "Both OPENAI_API_KEY and DASHSCOPE_API_KEY are set.\n"
        "Pick a backend:\n"
        "  1) openai  (OpenAI gpt-4o-mini-tts)\n"
        "  2) qwen    (DashScope qwen3-tts-flash)\n"
    )
    if not sys.stdin.isatty():
        sys.exit("Re-run with --backend openai or --backend qwen "
                 "(stdin is not a TTY; can't prompt).")
    pick = input("Choice [1/2]: ").strip()
    if pick in ("1", "openai"): return "openai"
    if pick in ("2", "qwen"):   return "qwen"
    sys.exit(f"Unknown choice: {pick!r}")


# ────────────────────────── OpenAI backend ──────────────────────────


def openai_tts(text, dest, api_key, model, voice, instructions, speed):
    body = {
        "model": model,
        "voice": voice,
        "input": text,
        "response_format": "mp3",
        "speed": speed,
    }
    if instructions:
        body["instructions"] = instructions
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode("utf-8"),
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            audio = resp.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"OpenAI TTS {e.code} for {dest.name}:\n"
                 f"{e.read().decode(errors='replace')}")
    dest.write_bytes(audio)


# ────────────────────────── Qwen / DashScope backend ──────────────────────────


def detect_language(text: str) -> str:
    """Heuristic: return 'Chinese' if the text has any CJK ideographs,
    else 'English'. Qwen3-TTS accepts both via the language_type field —
    setting it accurately helps prosody."""
    for ch in text:
        if "一" <= ch <= "鿿":
            return "Chinese"
    return "English"


def qwen_tts(text, dest, api_key, model, voice, region, *, want_mp3=True):
    """Two-step: POST text → get OSS URL → GET wav → optionally convert
    to mp3 via ffmpeg. The URL has a 24-hour validity but we use it
    immediately."""
    host = QWEN_HOSTS.get(region) or sys.exit(f"unknown region {region!r}")
    body = {
        "model": model,
        "input": {
            "text": text,
            "voice": voice,
            "language_type": detect_language(text),
        },
    }
    req = urllib.request.Request(
        host + QWEN_PATH,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode("utf-8"),
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Qwen TTS {e.code} for {dest.name}:\n"
                 f"{e.read().decode(errors='replace')}")
    audio_url = data.get("output", {}).get("audio", {}).get("url")
    if not audio_url:
        sys.exit(f"Qwen TTS returned no audio URL for {dest.name}:\n"
                 f"{json.dumps(data, indent=2)[:500]}")
    # Download the wav (always wav from this endpoint as of qwen3-tts-flash).
    wav_bytes = urllib.request.urlopen(audio_url, timeout=300).read()
    if want_mp3 and dest.suffix.lower() == ".mp3":
        # Convert wav → mp3 via ffmpeg so downstream pipelines stay uniform.
        if not shutil.which("ffmpeg"):
            sys.exit("ffmpeg not found on PATH; needed to convert Qwen wav → mp3. "
                     "Install ffmpeg or pass --out-format wav.")
        wav_tmp = dest.with_suffix(".wav.tmp")
        wav_tmp.write_bytes(wav_bytes)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-i", str(wav_tmp), "-codec:a", "libmp3lame", "-qscale:a", "2",
             str(dest)],
            check=True,
        )
        wav_tmp.unlink()
    else:
        # Direct wav output (preserve original sample rate / bit depth).
        dest.write_bytes(wav_bytes)


# ────────────────────────── orchestration ──────────────────────────


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--scripts-dir", type=Path, default=Path("scripts"))
    p.add_argument("--out-dir",     type=Path, default=Path("audio"))
    p.add_argument("--backend", choices=["auto", "openai", "qwen"], default="auto")
    p.add_argument("--region",  choices=["cn", "intl", "us"], default=None,
                   help="DashScope region (qwen backend only). "
                        "Default: $DASHSCOPE_REGION or 'cn'.")
    p.add_argument("--voice", default=None,
                   help="Voice name. Backend-specific defaults: "
                        "openai=ash, qwen=Cherry.")
    p.add_argument("--model", default=None,
                   help="Model name. Backend-specific defaults: "
                        "openai=gpt-4o-mini-tts, qwen=qwen3-tts-flash.")
    p.add_argument("--speed", type=float, default=1.0,
                   help="Speech speed (OpenAI only). Default 1.0.")
    p.add_argument("--instructions", default=DEFAULT_INSTRUCTIONS,
                   help="Speaking-style instructions (OpenAI only).")
    p.add_argument("--out-format", choices=["mp3", "wav"], default="mp3",
                   help="Output format. Qwen returns wav natively; we convert "
                        "to mp3 via ffmpeg when --out-format mp3 (default).")
    p.add_argument("--env", type=Path, default=Path(".env"))
    p.add_argument("--only", default=None,
                   help="Comma-separated scene names to (re)generate; "
                        "omit to process all .txt files.")
    args = p.parse_args()

    if not args.scripts_dir.exists():
        sys.exit(f"Scripts directory not found: {args.scripts_dir}")

    env_file = load_env(args.env)
    backend  = pick_backend(args.backend, env_file)
    voice    = args.voice or DEFAULT_VOICE[backend]
    model    = args.model or DEFAULT_MODEL[backend]
    region   = args.region or os.environ.get("DASHSCOPE_REGION") or \
               env_file.get("DASHSCOPE_REGION") or "cn"

    if backend == "openai":
        api_key = resolve_key("OPENAI_API_KEY", env_file)
        host_info = "OpenAI api.openai.com"
    else:
        api_key = resolve_key("DASHSCOPE_API_KEY", env_file)
        host_info = f"DashScope ({region}) {QWEN_HOSTS[region]}"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    scripts = sorted(args.scripts_dir.glob("*.txt"))
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        scripts = [s for s in scripts if s.stem in wanted]
    if not scripts:
        sys.exit(f"No matching .txt scripts in {args.scripts_dir}")

    print(f"Backend: {backend} → {host_info}")
    print(f"Voice:   {voice} · Model: {model}")
    print(f"Scripts: {args.scripts_dir} ({len(scripts)} files)")
    print(f"Out:     {args.out_dir} ({args.out_format})\n")

    suffix = ".mp3" if args.out_format == "mp3" else ".wav"

    for script_path in scripts:
        scene = script_path.stem
        text = script_path.read_text().strip()
        if not text:
            print(f"  ⚠ {scene} · empty file, skipping")
            continue
        wc = len(text.split())
        dest = args.out_dir / f"{scene}{suffix}"
        print(f"  ▶ {scene:18s} · {wc:>4} words", end=" ", flush=True)
        if backend == "openai":
            openai_tts(text, dest, api_key,
                       model, voice, args.instructions, args.speed)
        else:
            qwen_tts(text, dest, api_key,
                     model, voice, region,
                     want_mp3=(args.out_format == "mp3"))
        kb = dest.stat().st_size / 1024
        print(f"→ {kb:7.1f} KB")

    print("\nDone.")


if __name__ == "__main__":
    main()
