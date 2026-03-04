# -*- coding: utf-8 -*-
"""Runtime hook to configure paths for PyInstaller bundle."""
import os
import sys
from pathlib import Path


def _setup_paths():
    if getattr(sys, "frozen", False):
        # Add bundle's internal paths
        bundle_dir = Path(sys._MEIPASS)

        # Add copaw package to path
        copaw_dir = bundle_dir / "copaw"
        if copaw_dir.exists() and str(copaw_dir) not in sys.path:
            sys.path.insert(0, str(copaw_dir.parent))


_setup_paths()