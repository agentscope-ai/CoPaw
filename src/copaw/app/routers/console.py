# -*- coding: utf-8 -*-
"""Console API: push messages for cron text bubbles on the frontend."""

import asyncio
import os
import signal

from fastapi import APIRouter, Query


router = APIRouter(prefix="/console", tags=["console"])


@router.get("/push-messages")
async def get_push_messages(
    session_id: str | None = Query(None, description="Optional session id"),
):
    """
    Return pending push messages. Without session_id: recent messages
    (all sessions, last 60s), not consumed so every tab sees them.
    """
    from ..console_push_store import get_recent, take

    if session_id:
        messages = await take(session_id)
    else:
        messages = await get_recent()
    return {"messages": messages}


@router.post("/shutdown")
async def shutdown_backend():
    """
    Gracefully shutdown the backend (for desktop app).

    This endpoint is called by the Tauri shell when the user closes
    the application window, allowing the backend to clean up resources.
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Shutdown requested via API")

    async def do_shutdown():
        """Perform the actual shutdown after sending response."""
        await asyncio.sleep(0.5)
        logger.info("Initiating graceful shutdown...")
        os.kill(os.getpid(), signal.SIGTERM)

    # Schedule shutdown after response is sent
    asyncio.create_task(do_shutdown())

    return {"status": "shutting down", "message": "Backend is shutting down gracefully"}
