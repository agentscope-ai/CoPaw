# -*- coding: utf-8 -*-
import importlib
import logging
import os
import time

from .utils.logging import setup_logger

# Fallback before we can safely read canonical constant definitions.
LOG_LEVEL_ENV = "COPAW_LOG_LEVEL"

_bootstrap_err: Exception | None = None
try:
    # Load persisted env vars before importing modules that read env-backed
    # constants at import time (e.g., WORKING_DIR).
    from .envs import load_envs_into_environ

    load_envs_into_environ()
except Exception as exc:
    # Best effort: package import should not fail if env bootstrap fails.
    _bootstrap_err = exc

if _bootstrap_err is None:
    try:
        constant_module = importlib.import_module(
            ".constant",
            __package__,
        )
        LOG_LEVEL_ENV = getattr(
            constant_module,
            "LOG_LEVEL_ENV",
            LOG_LEVEL_ENV,
        )
    except Exception:
        # Keep fallback literal if canonical import unexpectedly fails.
        pass

_t0 = time.perf_counter()
setup_logger(os.environ.get(LOG_LEVEL_ENV, "info"))
if _bootstrap_err is not None:
    logging.getLogger(__name__).warning(
        "copaw: failed to load persisted envs on init: %s",
        _bootstrap_err,
    )
logging.getLogger(__name__).debug(
    "%.3fs package init",
    time.perf_counter() - _t0,
)
