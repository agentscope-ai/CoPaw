# -*- coding: utf-8 -*-
"""
macOS .app entry point: run CoPaw server (copaw app) with default options.
Used as PyInstaller entry when building the DMG bundle.
"""
from __future__ import annotations


def main() -> None:
    from copaw.cli.app_cmd import app_cmd

    # Invoke click command: bind to all interfaces for local access.
    app_cmd.main(args=["--host", "0.0.0.0"])


if __name__ == "__main__":
    main()
