# -*- coding: utf-8 -*-
# pylint:disable=too-many-return-statements
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
        logger.info("md_files root: __file__ path %s", base)
        return base
    if not getattr(sys, "frozen", False):
        logger.warning("md_files root: not found at %s (not frozen)", base)
        return base
    # PyInstaller one-file: datas under sys._MEIPASS
    if getattr(sys, "_MEIPASS", None):
        meipass = getattr(sys, "_MEIPASS")  # pylint: disable=protected-access
        fallback = Path(meipass).resolve() / "copaw" / "agents" / "md_files"
        if fallback.is_dir():
            logger.info("md_files root: _MEIPASS path %s", fallback)
            return fallback
    # .app layout: exe in Frameworks, data in copaw_resources or _internal
    exe_dir = Path(sys.executable).resolve().parent
    # Contents/Frameworks/copaw_resources/agents/md_files (build_dmg)
    frameworks = exe_dir / "copaw_resources" / "agents" / "md_files"
    if frameworks.is_dir():
        logger.info("md_files root: Frameworks path %s", frameworks)
        return frameworks
    # _internal/copaw/agents/md_files (PyInstaller output)
    internal = exe_dir / "_internal" / "copaw" / "agents" / "md_files"
    if internal.is_dir():
        logger.info("md_files root: _internal path %s", internal)
        return internal
    fallback = exe_dir / "copaw_resources" / "agents" / "md_files"
    if fallback.is_dir():
        logger.info("md_files root: exe_dir path %s", fallback)
        return fallback
    logger.warning(
        "md_files root: not found (tried %s, %s, %s, %s)",
        base,
        frameworks,
        internal,
        fallback,
    )
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
        logger.info(
            "copy_md_files: root=%s lang=%s (missing)",
            root,
            language,
        )
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
        logger.info(
            "copy_md_files: copied %s to %s",
            copied_files,
            WORKING_DIR,
        )
    else:
        logger.warning(
            "copy_md_files: no files copied (root=%s lang=%s)",
            root,
            language,
        )

    return copied_files
