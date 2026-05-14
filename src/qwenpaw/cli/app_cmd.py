# -*- coding: utf-8 -*-
from __future__ import annotations

import errno
import logging
import os
import socket

import click
import uvicorn

from ..constant import LOG_LEVEL_ENV
from ..config.utils import write_last_api
from ..utils.logging import setup_logger, SuppressPathAccessLogFilter


def _bind_preflight_error(host: str, port: int) -> OSError | None:
    """Return address-in-use errors before the app startup side effects."""
    try:
        addr_infos = socket.getaddrinfo(
            host,
            port,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror:
        return None

    for family, socktype, proto, _canonname, sockaddr in addr_infos:
        try:
            with socket.socket(family, socktype, proto) as sock:
                sock.bind(sockaddr)
                sock.listen(1)
        except OSError as exc:
            if exc.errno == errno.EADDRINUSE:
                return exc
    return None


def _ensure_bind_available(host: str, port: int) -> None:
    """Fail early when the configured HTTP bind is already occupied."""
    bind_error = _bind_preflight_error(host, port)
    if bind_error is None:
        return

    suggested_port = 8090 if port == 8088 else port + 1
    raise click.ClickException(
        f"Cannot start QwenPaw app because {host}:{port} is already in use. "
        "Stop the existing service with `qwenpaw shutdown`, or choose another "
        f"port such as `qwenpaw app --port {suggested_port}`.",
    )


@click.command("app")
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Bind host",
)
@click.option(
    "--port",
    default=8088,
    type=int,
    show_default=True,
    help="Bind port",
)
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev only)")
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(
        ["critical", "error", "warning", "info", "debug", "trace"],
        case_sensitive=False,
    ),
    show_default=True,
    help="Log level",
)
@click.option(
    "--hide-access-paths",
    multiple=True,
    default=("/console/push-messages",),
    show_default=True,
    help="Path substrings to hide from uvicorn access log (repeatable).",
)
@click.option(
    "--workers",
    type=int,
    default=None,
    help="[DEPRECATED] Number of worker processes. "
    "This option is deprecated and will be removed in a future version. "
    "QwenPaw always uses 1 worker.",
)
def app_cmd(
    host: str,
    port: int,
    reload: bool,
    workers: int,  # pylint: disable=unused-argument
    log_level: str,
    hide_access_paths: tuple[str, ...],
) -> None:
    """Run QwenPaw FastAPI app."""
    # Handle deprecated --workers parameter
    if workers is not None:
        click.echo(
            "WARNING: --workers option is deprecated and will be removed in "
            "a future version.",
            err=True,
        )
        click.echo(
            "   QwenPaw always uses 1 worker for stability. "
            "Your specified value will be ignored.",
            err=True,
        )
        click.echo(err=True)

    _ensure_bind_available(host, port)

    # Persist last used host/port for other terminals
    if host == "0.0.0.0":
        write_last_api("127.0.0.1", port)
    else:
        write_last_api(host, port)
    os.environ[LOG_LEVEL_ENV] = log_level

    # Signal reload mode to browser_control.py for Windows
    # compatibility: use sync Playwright + ThreadPool only when reload=True
    if reload:
        os.environ["QWENPAW_RELOAD_MODE"] = "1"
    else:
        os.environ.pop("QWENPAW_RELOAD_MODE", None)

    setup_logger(log_level)
    if log_level in ("debug", "trace"):
        from .main import log_init_timings

        log_init_timings()

    paths = [p for p in hide_access_paths if p]
    if paths:
        logging.getLogger("uvicorn.access").addFilter(
            SuppressPathAccessLogFilter(paths),
        )

    uvicorn.run(
        "qwenpaw.app._app:app",
        host=host,
        port=port,
        reload=reload,
        workers=1,
        log_level=log_level,
    )
