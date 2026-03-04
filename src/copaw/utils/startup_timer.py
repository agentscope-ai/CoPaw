# -*- coding: utf-8 -*-
"""Startup timing utility for performance analysis.

Provides a global timer that tracks individual startup stages and produces
a structured summary showing elapsed time and percentage for each stage.

Usage in lifespan:
    timer = get_startup_timer()
    with timer.stage("runner.start"):
        await runner.start()
    timer.summary()

Usage for import profiling (CLI):
    copaw app --profile-startup
"""
from __future__ import annotations

import importlib
import sys
import time
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class StartupTimer:
    """Timer for tracking startup performance.
    
    Usage:
        timer = StartupTimer()
        
        with timer.stage("config_load"):
            load_config()
            
        with timer.stage("memory_init"):
            await memory_manager.start()
            
        timer.summary()
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.start_time: Optional[float] = None
        self.stages: list[tuple[str, float, float]] = []
        
    def start(self) -> None:
        """Start the overall timer."""
        self.start_time = time.perf_counter()
        if self.enabled:
            logger.info("[startup] timer started")
    
    @contextmanager
    def stage(self, name: str):
        """Context manager for timing a startup stage."""
        if not self.enabled:
            yield
            return
            
        stage_start = time.perf_counter()
        logger.info("[startup] stage=%s status=started", name)
        
        try:
            yield
        finally:
            elapsed = time.perf_counter() - stage_start
            self.stages.append((name, stage_start, elapsed))
            total = time.perf_counter() - self.start_time if self.start_time else 0
            logger.info(
                "[startup] stage=%s elapsed_ms=%.1f total_ms=%.1f",
                name, elapsed * 1000, total * 1000
            )
    
    def mark(self, name: str) -> None:
        """Mark a point in time without a context manager."""
        if not self.enabled or self.start_time is None:
            return
            
        elapsed = time.perf_counter() - self.start_time
        self.stages.append((name, time.perf_counter(), 0))
        logger.info("[startup] mark=%s total_ms=%.1f", name, elapsed * 1000)
    
    def summary(self) -> None:
        """Log a summary of all stages."""
        if not self.enabled or not self.stages:
            return
            
        total_time = time.perf_counter() - self.start_time if self.start_time else 0
        
        logger.info("[startup] ====== Startup Summary ======")
        logger.info("[startup] Total time: %.1f ms", total_time * 1000)
        logger.info("[startup] Stages breakdown:")
        
        for name, _, elapsed in self.stages:
            if elapsed > 0:
                pct = (elapsed / total_time * 100) if total_time > 0 else 0
                logger.info(
                    "[startup]   %-30s %7.1f ms  (%4.1f%%)",
                    name, elapsed * 1000, pct
                )
        
        logger.info("[startup] ================================")


# Global timer instance
_global_timer: Optional[StartupTimer] = None


def get_startup_timer(enabled: bool = True) -> StartupTimer:
    """Get or create the global startup timer."""
    global _global_timer
    if _global_timer is None:
        _global_timer = StartupTimer(enabled=enabled)
        _global_timer.start()
    return _global_timer


def reset_startup_timer(enabled: bool = True) -> StartupTimer:
    """Reset and restart the global startup timer."""
    global _global_timer
    _global_timer = StartupTimer(enabled=enabled)
    _global_timer.start()
    return _global_timer


def profile_imports(module_name: str, top_n: int = 20) -> None:
    """Profile import times for a given module and its dependencies.
    
    Patches importlib to measure time spent in each import, then
    imports the target module and prints a sorted report.
    
    Args:
        module_name: Fully qualified module name to profile (e.g. "copaw.app._app")
        top_n: Number of slowest imports to show
    """
    timings: dict[str, float] = {}
    original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else importlib.__import__
    
    def _timed_import(name, *args, **kwargs):
        already_loaded = name in sys.modules
        t0 = time.perf_counter()
        result = original_import(name, *args, **kwargs)
        elapsed = time.perf_counter() - t0
        if not already_loaded and elapsed > 0.001:  # Only track imports > 1ms
            timings[name] = timings.get(name, 0) + elapsed
        return result
    
    import builtins
    builtins.__import__ = _timed_import
    
    try:
        t0 = time.perf_counter()
        importlib.import_module(module_name)
        total = time.perf_counter() - t0
    finally:
        builtins.__import__ = original_import
    
    # Sort by time descending
    sorted_timings = sorted(timings.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n{'='*60}")
    print(f"  Import Profile: {module_name}")
    print(f"  Total import time: {total*1000:.1f} ms")
    print(f"{'='*60}")
    print(f"  {'Module':<40s} {'Time (ms)':>10s}")
    print(f"  {'-'*40} {'-'*10}")
    
    for name, elapsed in sorted_timings[:top_n]:
        print(f"  {name:<40s} {elapsed*1000:>10.1f}")
    
    if len(sorted_timings) > top_n:
        rest_time = sum(t for _, t in sorted_timings[top_n:])
        print(f"  {'... (remaining)' :<40s} {rest_time*1000:>10.1f}")
    
    print(f"{'='*60}\n")