#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Generate icon.icns from scripts/pack/assets/icon.svg (copaw-symbol, rounded,
# transparent bg) for macOS app bundle.
# Uses macOS qlmanage + sips + iconutil (no extra deps). Run from repo root.
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS = REPO_ROOT / "scripts" / "pack" / "assets"
SVG = ASSETS / "icon.svg"
ICNS = ASSETS / "icon.icns"
SIZES = (16, 32, 64, 128, 256, 512)


def main() -> int:
    if sys.platform != "darwin":
        print("icon.icns can only be generated on macOS (qlmanage, iconutil).")
        return 0
    if not SVG.exists():
        print(f"Missing {SVG}", file=sys.stderr)
        return 1
    ASSETS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        png_1024 = tmp / "icon.png"
        subprocess.run(
            ["qlmanage", "-t", "-s", "1024", "-o", str(tmp), str(SVG)],
            check=True,
            capture_output=True,
        )
        thumb = tmp / f"{SVG.name}.png"
        if not thumb.exists():
            print("qlmanage did not produce PNG", file=sys.stderr)
            return 1
        thumb.rename(png_1024)
        iconset = tmp / "CoPaw.iconset"
        iconset.mkdir()
        for s in SIZES:
            out1 = iconset / f"icon_{s}x{s}.png"
            subprocess.run(
                [
                    "sips",
                    "-z",
                    str(s),
                    str(s),
                    str(png_1024),
                    "--out",
                    str(out1),
                ],
                check=True,
                capture_output=True,
            )
            s2 = s * 2
            out2 = iconset / f"icon_{s}x{s}@2x.png"
            subprocess.run(
                [
                    "sips",
                    "-z",
                    str(s2),
                    str(s2),
                    str(png_1024),
                    "--out",
                    str(out2),
                ],
                check=True,
                capture_output=True,
            )
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(ICNS)],
            check=True,
        )
    print(f"Wrote {ICNS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
