# -*- coding: utf-8 -*-
# pylint:disable=unused-import
"""
PyInstaller runtime hook: fix opentelemetry context loading in frozen apps.

In frozen envs entry_points() for "opentelemetry_context" is often empty,
so _load_runtime_context() raises StopIteration. We patch
opentelemetry.util._importlib_metadata.entry_points to return a fake
contextvars_context entry when the real one is missing.
"""
from __future__ import annotations


def _install_patch() -> None:
    try:
        import opentelemetry.util._importlib_metadata as _otel_meta
    except ImportError:
        return
    _orig = _otel_meta.entry_points

    class _FakeContextEntry:
        def load(self):
            def _factory():
                from opentelemetry.context.contextvars_context import (
                    ContextVarsRuntimeContext,
                )

                return ContextVarsRuntimeContext()

            return _factory

    def _patched_entry_points(**params):
        out = _orig(**params)
        if params.get("group") != "opentelemetry_context":
            return out
        try:
            first = next(iter(out), None)
        except (StopIteration, TypeError):
            first = None
        if first is None:
            return iter([_FakeContextEntry()])
        return out

    _otel_meta.entry_points = _patched_entry_points


_install_patch()

# Pre-import chromadb after the patch so reme gets a valid module (avoids
# chromadb=None and AttributeError on chromadb.ClientAPI when reme loads).
# If this fails (e.g. on a different macOS than build host), surface the
# real error so users see e.g. "Library not loaded" instead of AttributeError.
try:
    import chromadb  # noqa: F401
    from chromadb.config import Settings  # noqa: F401
except Exception as _e:  # ImportError or OSError (dylib load fail)
    import sys
    import traceback

    sys.stderr.write(
        "CoPaw runtime hook: chromadb pre-import failed (app may crash next).\n",
    )
    traceback.print_exc(file=sys.stderr)
    raise
