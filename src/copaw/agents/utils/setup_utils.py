# -*- coding: utf-8 -*-
"""Setup and initialization utilities for agent configuration.

This module handles copying markdown configuration files to
the working directory.
"""
import logging
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _md_files_root() -> Path:
    """Root of agents/md_files (works from source and PyInstaller bundle)."""
    base = Path(__file__).resolve().parent.parent / "md_files"
    if base.is_dir():
        return base
    if not getattr(sys, "frozen", False):
        return base
    # PyInstaller one-file: datas under sys._MEIPASS
    if getattr(sys, "_MEIPASS", None):
        meipass = getattr(sys, "_MEIPASS")  # pylint: disable=protected-access
        fallback = Path(meipass).resolve() / "copaw" / "agents" / "md_files"
        if fallback.is_dir():
            return fallback
    # PyInstaller one-folder: datas next to executable
    exe_dir = Path(sys.executable).resolve().parent
    fallback = exe_dir / "copaw" / "agents" / "md_files"
    if fallback.is_dir():
        return fallback
    return base


def copy_md_files(
    language: str,
    skip_existing: bool = False,
) -> list[str]:
    """Copy md files from agents/md_files to working directory.

    Args:
        language: Language code (e.g. 'en', 'zh')
        skip_existing: If True, skip files that already exist in working dir.

    Returns:
        List of copied file names.
    """
    from ...constant import WORKING_DIR

    root = _md_files_root()
    md_files_dir = root / language

    if not md_files_dir.exists():
        logger.warning(
            "MD files directory not found: %s, falling back to 'en'",
            md_files_dir,
        )
        md_files_dir = root / "en"
        if not md_files_dir.exists():
            logger.error("Default 'en' md files not found either")
            return []

    # Ensure working directory exists
    WORKING_DIR.mkdir(parents=True, exist_ok=True)

    # Copy all .md files to working directory
    copied_files: list[str] = []
    for md_file in md_files_dir.glob("*.md"):
        target_file = WORKING_DIR / md_file.name
        if skip_existing and target_file.exists():
            logger.debug("Skipped existing md file: %s", md_file.name)
            continue
        try:
            shutil.copy2(md_file, target_file)
            logger.debug("Copied md file: %s", md_file.name)
            copied_files.append(md_file.name)
        except Exception as e:
            logger.error(
                "Failed to copy md file '%s': %s",
                md_file.name,
                e,
            )

    if copied_files:
        logger.debug(
            "Copied %d md file(s) [%s] to %s",
            len(copied_files),
            language,
            WORKING_DIR,
        )

    return copied_files
