# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name,unused-argument
import asyncio
import mimetypes
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agentscope_runtime.engine.app import AgentApp

from .runner import AgentRunner
from ..config import (  # pylint: disable=no-name-in-module
    load_config,
    update_last_dispatch,
    ConfigWatcher,
)
from ..config.utils import get_jobs_path, get_chats_path, get_config_path, get_heartbeat_config
from ..constant import DOCS_ENABLED, LOG_LEVEL_ENV, CORS_ORIGINS
from ..__version__ import __version__
from ..utils.logging import setup_logger
from ..utils.startup_timer import get_startup_timer
from .channels import ChannelManager  # pylint: disable=no-name-in-module
from .channels.utils import make_process_from_runner
from .mcp import MCPClientManager, MCPConfigWatcher  # MCP hot-reload support
from .runner.repo.json_repo import JsonChatRepository
from .crons.repo.json_repo import JsonJobRepository
from .crons.manager import CronManager
from .runner.manager import ChatManager
from .routers import router as api_router
from ..envs import load_envs_into_environ

# Apply log level on load so reload child process gets same level as CLI.
logger = setup_logger(os.environ.get(LOG_LEVEL_ENV, "info"))

# Ensure static assets are served with browser-compatible MIME types across
# platforms (notably Windows may miss .js/.mjs mappings).
mimetypes.init()
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/wasm", ".wasm")

# Load persisted env vars into os.environ at module import time
# so they are available before the lifespan starts.
load_envs_into_environ()

runner = AgentRunner()

agent_app = AgentApp(
    app_name="Friday",
    app_description="A helpful assistant",
    runner=runner,
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=too-many-statements
    timer = get_startup_timer(enabled=True)
    is_desktop_app = os.environ.get("COPAW_DESKTOP_APP", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    # Pass desktop mode to runner for lazy initialization
    runner.set_desktop_mode(is_desktop_app)
    
    with timer.stage("runner.start"):
        await runner.start()

    with timer.stage("config.load"):
        config = load_config()
    
    with timer.stage("mcp_manager.init"):
        mcp_manager = MCPClientManager()
    
    with timer.stage("channel_manager.from_config"):
        channel_manager = ChannelManager.from_config(
            process=make_process_from_runner(runner),
            config=config,
            on_last_dispatch=update_last_dispatch,
        )
    
    # Lazy init CronManager: skip if no jobs and heartbeat disabled
    with timer.stage("cron_manager.check"):
        repo = JsonJobRepository(get_jobs_path())
        jobs_file = await repo.load()
        hb = get_heartbeat_config()
        has_enabled_jobs = any(getattr(j, "enabled", True) for j in jobs_file.jobs)
        hb_enabled = getattr(hb, "enabled", False)
        
        if has_enabled_jobs or hb_enabled:
            cron_manager = CronManager(
                repo=repo,
                runner=runner,
                channel_manager=channel_manager,
                timezone="UTC",
            )
            logger.info("CronManager initialized: jobs=%d heartbeat=%s", 
                        len(jobs_file.jobs), hb_enabled)
        else:
            cron_manager = None
            logger.info("CronManager skipped: no jobs and heartbeat disabled")
    
    with timer.stage("chat_manager.init"):
        chat_repo = JsonChatRepository(get_chats_path())
        chat_manager = ChatManager(
            repo=chat_repo,
        )

    runner.set_chat_manager(chat_manager)
    
    with timer.stage("config_watcher.init"):
        config_watcher = ConfigWatcher(
            channel_manager=channel_manager,
            cron_manager=cron_manager,
        )
    mcp_watcher = None

    async def _start_noncritical_services() -> None:
        with timer.stage("mcp.init_from_config"):
            if hasattr(config, "mcp"):
                try:
                    await mcp_manager.init_from_config(config.mcp)
                    runner.set_mcp_manager(mcp_manager)
                    logger.debug("MCP client manager initialized")
                except Exception:
                    logger.exception("Failed to initialize MCP manager")

        with timer.stage("channel_manager.start_all"):
            await channel_manager.start_all()

        with timer.stage("cron_manager.start"):
            if cron_manager is not None:
                await cron_manager.start()
            else:
                logger.debug("CronManager start skipped")

        with timer.stage("config_watcher.start"):
            await config_watcher.start()

        with timer.stage("mcp_watcher.start"):
            nonlocal mcp_watcher
            if hasattr(config, "mcp"):
                try:
                    mcp_watcher = MCPConfigWatcher(
                        mcp_manager=mcp_manager,
                        config_loader=load_config,
                        config_path=get_config_path(),
                    )
                    await mcp_watcher.start()
                    app.state.mcp_watcher = mcp_watcher
                    logger.debug("MCP config watcher started")
                except Exception:
                    logger.exception("Failed to start MCP watcher")

    # expose to endpoints
    app.state.runner = runner
    app.state.channel_manager = channel_manager
    app.state.cron_manager = cron_manager
    app.state.chat_manager = chat_manager
    app.state.config_watcher = config_watcher
    app.state.mcp_manager = mcp_manager
    app.state.mcp_watcher = mcp_watcher
    app.state.noncritical_task = None

    # In desktop runtime, unblock API quickly and initialize non-critical
    # services in background to reduce startup wait time.
    if is_desktop_app:
        logger.info("[startup] desktop fast path enabled: defer non-critical services")
        app.state.noncritical_task = asyncio.create_task(_start_noncritical_services())
        timer.mark("lifespan.ready")
    else:
        await _start_noncritical_services()
        app.state.mcp_watcher = mcp_watcher
        timer.mark("lifespan.ready")
    
    # Log startup summary
    timer.summary()

    try:
        yield
    finally:
        task = getattr(app.state, "noncritical_task", None)
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        # stop order: watchers -> cron -> channels -> mcp -> runner
        try:
            await config_watcher.stop()
        except Exception:
            pass
        if mcp_watcher:
            try:
                await mcp_watcher.stop()
            except Exception:
                pass
        if cron_manager is not None:
            try:
                await cron_manager.stop()
            except Exception:
                pass
        await channel_manager.stop_all()
        if mcp_manager:
            try:
                await mcp_manager.close_all()
            except Exception:
                pass
        await runner.stop()


app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)

# CORS:
# - If COPAW_CORS_ORIGINS is explicitly set, honor it.
# - Otherwise, enable safe desktop defaults so tauri:// / tauri.localhost can
#   call local API endpoints without failing OPTIONS preflight.
if CORS_ORIGINS:
    origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "tauri://localhost",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "null",
            "http://127.0.0.1:8088",
            "http://localhost:8088",
        ],
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|tauri\.localhost)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Console static dir: env, or copaw package data (console), or cwd.
_CONSOLE_STATIC_ENV = "COPAW_CONSOLE_STATIC_DIR"


def _resolve_console_static_dir() -> str:
    if os.environ.get(_CONSOLE_STATIC_ENV):
        return os.environ[_CONSOLE_STATIC_ENV]
    # Shipped dist lives in copaw package as static data (not a Python pkg).
    pkg_dir = Path(__file__).resolve().parent.parent
    candidate = pkg_dir / "console"
    if candidate.is_dir() and (candidate / "index.html").exists():
        return str(candidate)
    cwd = Path(os.getcwd())
    for subdir in ("console/dist", "console_dist"):
        candidate = cwd / subdir
        if candidate.is_dir() and (candidate / "index.html").exists():
            return str(candidate)
    return str(cwd / "console" / "dist")


_CONSOLE_STATIC_DIR = _resolve_console_static_dir()
_CONSOLE_INDEX = (
    Path(_CONSOLE_STATIC_DIR) / "index.html" if _CONSOLE_STATIC_DIR else None
)
logger.info(f"STATIC_DIR: {_CONSOLE_STATIC_DIR}")


@app.get("/")
def read_root():
    if _CONSOLE_INDEX and _CONSOLE_INDEX.exists():
        from fastapi.responses import FileResponse

        return FileResponse(_CONSOLE_INDEX)
    return {"message": "Hello World"}


@app.get("/api/version")
def get_version():
    """Return the current CoPaw version."""
    return {"version": __version__}


@app.get("/api/health")
def get_health():
    """Lightweight health endpoint for desktop startup readiness checks."""
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")

app.include_router(
    agent_app.router,
    prefix="/api/agent",
    tags=["agent"],
)

# Mount console: root static files (logo.png etc.) then assets, then SPA
# fallback.
if os.path.isdir(_CONSOLE_STATIC_DIR):
    _console_path = Path(_CONSOLE_STATIC_DIR)

    @app.get("/logo.png")
    def _console_logo():
        f = _console_path / "logo.png"
        if f.is_file():
            from fastapi.responses import FileResponse

            return FileResponse(f, media_type="image/png")

        raise HTTPException(status_code=404, detail="Not Found")

    @app.get("/copaw-symbol.svg")
    def _console_icon():
        f = _console_path / "copaw-symbol.svg"
        if f.is_file():
            from fastapi.responses import FileResponse

            return FileResponse(f, media_type="image/svg+xml")

        raise HTTPException(status_code=404, detail="Not Found")

    _assets_dir = _console_path / "assets"
    if _assets_dir.is_dir():
        from fastapi.staticfiles import StaticFiles

        app.mount(
            "/assets",
            StaticFiles(directory=str(_assets_dir)),
            name="assets",
        )

    @app.get("/{full_path:path}")
    def _console_spa(full_path: str):
        if _CONSOLE_INDEX and _CONSOLE_INDEX.exists():
            from fastapi.responses import FileResponse

            return FileResponse(_CONSOLE_INDEX)

        raise HTTPException(status_code=404, detail="Not Found")
