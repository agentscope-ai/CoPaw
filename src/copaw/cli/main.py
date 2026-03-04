# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import logging
import sys
import time

import click

# On Windows, force UTF-8 for stdout/stderr so cron and other commands
# can handle Chinese and other non-ASCII (Linux is UTF-8 by default).
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

# pylint: disable=wrong-import-position

logger = logging.getLogger(__name__)
# Store init timings so app_cmd can re-log after setting log level to debug.
_init_timings: list[tuple[str, float]] = []
_t0_main = time.perf_counter()
_init_timings.append(("main.py loaded", 0.0))


def _record(label: str, elapsed: float) -> None:
    _init_timings.append((label, elapsed))
    logger.debug("%.3fs %s", elapsed, label)


# Timed imports below: order and placement are intentional (E402/C0413).
_t = time.perf_counter()
from ..config.utils import read_last_api  # noqa: E402

_record("..config.utils", time.perf_counter() - _t)

_total = time.perf_counter() - _t0_main
_init_timings.append(("(total imports)", _total))
logger.debug("%.3fs (total imports)", _total)


def log_init_timings() -> None:
    """Emit init timing debug lines after setup_logger(debug) in app_cmd."""
    for label, elapsed in _init_timings:
        logger.debug("%.3fs %s", elapsed, label)


class LazyGroup(click.Group):
    """Click group that lazily imports command objects on first use."""

    def __init__(self, *args, lazy_commands: dict[str, tuple[str, str]], **kwargs):
        super().__init__(*args, **kwargs)
        self._lazy_commands = lazy_commands

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(self._lazy_commands.keys())

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        target = self._lazy_commands.get(cmd_name)
        if target is None:
            return None

        module_name, attr_name = target
        t0 = time.perf_counter()
        try:
            module = importlib.import_module(module_name, __package__)
            cmd = getattr(module, attr_name)
        except Exception as exc:
            error_text = f"Failed to load command '{cmd_name}': {exc}"

            @click.command(name=cmd_name)
            def _failed_command() -> None:
                raise click.ClickException(error_text)

            return _failed_command

        _record(f"lazy .{cmd_name}", time.perf_counter() - t0)
        return cmd


@click.group(
    cls=LazyGroup,
    lazy_commands={
        "app": (".app_cmd", "app_cmd"),
        "channels": (".channels_cmd", "channels_group"),
        "chats": (".chats_cmd", "chats_group"),
        "clean": (".clean_cmd", "clean_cmd"),
        "cron": (".cron_cmd", "cron_group"),
        "env": (".env_cmd", "env_group"),
        "init": (".init_cmd", "init_cmd"),
        "models": (".providers_cmd", "models_group"),
        "skills": (".skills_cmd", "skills_group"),
        "uninstall": (".uninstall_cmd", "uninstall_cmd"),
    },
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option("--host", default=None, help="API Host")
@click.option(
    "--port",
    default=None,
    type=int,
    help="API Port",
)
@click.pass_context
def cli(ctx: click.Context, host: str | None, port: int | None) -> None:
    """CoPaw CLI."""
    # default from last run if not provided
    last = read_last_api()
    if host is None or port is None:
        if last:
            host = host or last[0]
            port = port or last[1]

    # final fallback
    host = host or "127.0.0.1"
    port = port or 8088

    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["port"] = port
