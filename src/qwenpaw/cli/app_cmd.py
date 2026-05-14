# -*- coding: utf-8 -*-
from __future__ import annotations

import ipaddress
import logging
import os

import click
import uvicorn

from ..constant import LOG_LEVEL_ENV, EnvVarLoader
from ..config.utils import write_last_api
from ..utils.logging import setup_logger, SuppressPathAccessLogFilter

_LOOPBACK_HOSTNAMES = {"localhost"}
_TRUTHY_ENV_VALUES = {"true", "1", "yes"}


def _env_truthy(name: str) -> bool:
    return EnvVarLoader.get_str(name, "").strip().lower() in _TRUTHY_ENV_VALUES


def _is_non_loopback_bind(host: str) -> bool:
    normalized = (host or "").strip().lower().rstrip(".")
    if normalized in _LOOPBACK_HOSTNAMES:
        return False
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1]
    try:
        return not ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        # Hostnames can resolve to public interfaces, so require an explicit
        # auth/proxy/override path unless it is a known loopback name.
        return True


def _guard_public_bind_without_auth(
    host: str,
    allow_unauth_public: bool,
) -> None:
    if allow_unauth_public or not _is_non_loopback_bind(host):
        return
    if _env_truthy("QWENPAW_AUTH_ENABLED"):
        return
    if _env_truthy("QWENPAW_TRUST_PROXY_AUTH"):
        return

    raise click.ClickException(
        "Refusing to bind QwenPaw to non-loopback host "
        f"'{host}' while authentication is disabled. Set "
        "QWENPAW_AUTH_ENABLED=true, bind to 127.0.0.1 behind your "
        "reverse proxy/Tailscale, set QWENPAW_TRUST_PROXY_AUTH=1 when "
        "external auth terminates before QwenPaw, or pass "
        "--allow-unauth-public to override.",
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
    "--allow-unauth-public",
    is_flag=True,
    help="Allow a non-loopback bind while built-in auth is disabled.",
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
    allow_unauth_public: bool,
) -> None:
    """Run QwenPaw FastAPI app."""
    # Handle deprecated --workers parameter
    if workers is not None:
        click.echo(
            "⚠️  WARNING: --workers option is deprecated and will be removed "
            "in a future version.",
            err=True,
        )
        click.echo(
            "   QwenPaw always uses 1 worker for stability. "
            "Your specified value will be ignored.",
            err=True,
        )
        click.echo(err=True)

    _guard_public_bind_without_auth(host, allow_unauth_public)

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
