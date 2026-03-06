#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a temporary conda env, install copaw from repo, run conda-pack.
Used by build_macos.sh and build_win.ps1. Run from repo root.
"""
from __future__ import annotations

import argparse
import random
import string
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PREFIX = "copaw_pack_"


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd or REPO_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Conda-pack CoPaw (temp env).",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output archive path (e.g. .tar.gz)",
    )
    parser.add_argument(
        "--format",
        "-f",
        default="infer",
        choices=["infer", "zip", "tar.gz", "tgz"],
        help="Archive format (default: infer from --output extension)",
    )
    parser.add_argument(
        "--python",
        default="3.10",
        help="Python version for conda env (default: 3.10)",
    )
    args = parser.parse_args()
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    env_name = (
        f"{ENV_PREFIX}{''.join(random.choices(string.ascii_lowercase, k=8))}"
    )

    try:
        _run(
            ["conda", "create", "-n", env_name, f"python={args.python}", "-y"],
        )
        _run(
            [
                "conda",
                "run",
                "-n",
                env_name,
                "pip",
                "install",
                ".[full]",
            ],
        )
        _run(
            [
                "conda",
                "run",
                "-n",
                env_name,
                "conda",
                "install",
                "-y",
                "conda-pack",
            ],
        )
        pack_cmd = [
            "conda",
            "run",
            "-n",
            env_name,
            "conda-pack",
            "-n",
            env_name,
            "-o",
            str(out_path),
        ]
        if args.format != "infer":
            pack_cmd.extend(["--format", args.format])
        _run(pack_cmd)
        print(f"Packed to {out_path}")
    finally:
        _run(["conda", "env", "remove", "-n", env_name, "-y"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
