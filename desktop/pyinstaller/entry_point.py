# -*- coding: utf-8 -*-
"""Entry point for PyInstaller bundled CoPaw backend."""
import os
import sys
from pathlib import Path


def setup_environment():
    """Set up environment for bundled app."""
    # Determine if running in PyInstaller bundle
    if getattr(sys, "frozen", False):
        # Running as compiled
        bundle_dir = Path(sys._MEIPASS)

        # Set console static directory
        console_dir = bundle_dir / "copaw" / "console"
        if console_dir.exists():
            os.environ["COPAW_CONSOLE_STATIC_DIR"] = str(console_dir)

        # Set working directory (user's home, not bundle)
        home = Path.home() / ".copaw"
        os.environ["COPAW_WORKING_DIR"] = str(home)
        # Mark desktop runtime so backend startup can avoid rewriting config.
        os.environ["COPAW_DESKTOP_APP"] = "1"

        # Ensure working directory exists
        home.mkdir(parents=True, exist_ok=True)

        # Configure playwright browser path (will be downloaded on first use)
        browsers_path = home / "playwright-browsers"
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)


def main():
    """Main entry point."""
    setup_environment()

    # Fast path for desktop backend startup: avoid importing full CLI tree.
    from copaw.cli.app_cmd import app_cmd

    # Default to app command with sensible defaults for desktop.
    if len(sys.argv) == 1:
        app_cmd.main(
            args=["--host", "127.0.0.1", "--port", "8088"],
            prog_name="copaw app",
        )
        return

    # Tauri sidecar invokes: copaw-backend app --host ... --port ...
    if sys.argv[1] == "app":
        app_cmd.main(args=sys.argv[2:], prog_name="copaw app")
        return

    # Fallback to full CLI for non-app commands.
    from copaw.cli.main import cli
    cli()


if __name__ == "__main__":
    main()
