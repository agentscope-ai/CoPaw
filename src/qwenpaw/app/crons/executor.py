# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from ..inbox_trace_store import (
    append_trace_from_session_delta,
    create_trace,
    finalize_trace,
    read_session_messages,
)
from .models import CronJobSpec

logger = logging.getLogger(__name__)


def _save_checkpoint(
    checkpoint_dir: str,
    job_id: str,
    session_id: str,
    messages: list[dict[str, Any]],
    compressed_summary: str = "",
) -> str:
    """Save a checkpoint of session state to disk.

    Args:
        checkpoint_dir: Directory for checkpoint files.
        job_id: Cron job ID.
        session_id: Session ID being checkpointed.
        messages: List of session messages.
        compressed_summary: Current compressed summary text.

    Returns:
        Path to the saved checkpoint file.
    """
    now = datetime.now(tz=timezone.utc)
    ts = now.strftime("%Y%m%d-%H%M%S")
    cp_dir = Path(checkpoint_dir)
    cp_dir.mkdir(parents=True, exist_ok=True)
    filename = f"cron-{job_id}-{ts}.json"
    filepath = cp_dir / filename

    checkpoint_data = {
        "job_id": job_id,
        "session_id": session_id,
        "timestamp": now.isoformat(),
        "message_count": len(messages),
        "compressed_summary": compressed_summary,
        "messages": messages,
    }
    filepath.write_text(
        json.dumps(checkpoint_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "Checkpoint saved: %s (%d messages)",
        filepath,
        len(messages),
    )
    return str(filepath)


def _build_checkpoint_summary(
    messages: list[dict[str, Any]],
    compressed_summary: str = "",
) -> str:
    """Build a concise summary string from checkpoint data for injection.

    This provides just enough context for the agent to continue work
    without the full message history.
    """
    lines = ["[Previous session checkpoint summary]"]

    if compressed_summary:
        lines.append(f"Compressed summary:\n{compressed_summary}")

    # Extract last few user/assistant text exchanges for continuity
    recent_exchanges = []
    for msg in messages[-10:]:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if isinstance(content, list):
            texts = [
                b.get("text", "")
                for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            ]
            content = "\n".join(texts)
        if isinstance(content, str) and content.strip():
            preview = content.strip()[:500]
            recent_exchanges.append(f"  [{role}] {preview}")
    if recent_exchanges:
        lines.append("Recent exchanges:")
        lines.extend(recent_exchanges)

    lines.append(
        "This is a fresh session after auto-reset. "
        "Continue your task from where you left off.",
    )
    return "\n\n".join(lines)


class CronExecutor:
    def __init__(self, *, runner: Any, channel_manager: Any):
        self._runner = runner
        self._channel_manager = channel_manager

    # pylint: disable=too-many-statements,too-many-branches
    async def execute(self, job: CronJobSpec) -> dict[str, Any]:
        """Execute one job once.

        - task_type text: send fixed text to channel
        - task_type agent: ask agent with prompt, send reply to channel (
            stream_query + send_event)

        When auto_reset=True, each trigger:
        1. Saves a checkpoint of the current session
        2. Creates a fresh session_id with run_id
        3. Injects checkpoint summary into the new session's first message
        """
        target_user_id = job.dispatch.target.user_id
        target_session_id = job.dispatch.target.session_id
        target_channel = job.dispatch.channel
        dispatch_meta: Dict[str, Any] = dict(job.dispatch.meta or {})
        logger.info(
            "cron execute: job_id=%s channel=%s task_type=%s "
            "target_user_id=%s target_session_id=%s auto_reset=%s",
            job.id,
            target_channel,
            job.task_type,
            target_user_id[:40] if target_user_id else "",
            target_session_id[:40] if target_session_id else "",
            job.runtime.auto_reset,
        )

        if job.task_type == "text" and job.text:
            logger.info(
                "cron send_text: job_id=%s channel=%s len=%s",
                job.id,
                target_channel,
                len(job.text or ""),
            )
            text_delivery_error: str | None = None
            try:
                await self._channel_manager.send_text(
                    channel=target_channel,
                    user_id=target_user_id,
                    session_id=target_session_id,
                    text=job.text.strip(),
                    meta=dispatch_meta,
                )
            except Exception as e:  # pylint: disable=broad-except
                text_delivery_error = repr(e)
                logger.warning(
                    "cron text delivery failed: job_id=%s channel=%s error=%s",
                    job.id,
                    job.dispatch.channel,
                    text_delivery_error,
                )
            return {
                "task_type": "text",
                "run_id": None,
                "final_text": job.text.strip(),
                "delivery_status": (
                    "failed" if text_delivery_error else "success"
                ),
                "delivery_error": text_delivery_error,
            }

        # agent: run request as the dispatch target user so context matches
        logger.info(
            "cron agent: job_id=%s channel=%s stream_query then send_event",
            job.id,
            job.dispatch.channel,
        )
        assert job.request is not None
        req: Dict[str, Any] = job.request.model_dump(mode="json")

        req["channel"] = target_channel
        req["user_id"] = target_user_id or "cron"

        # Determine session_id based on share_session
        share_session = job.runtime.share_session
        if share_session:
            req["session_id"] = target_session_id or f"cron:{job.id}"
        else:
            # Use job.id (not run_id) so all runs of this job accumulate in the
            # same dedicated session, giving users a complete history.
            req["session_id"] = (
                f"{target_session_id}:cron:{job.id}"
                if target_session_id
                else f"cron:{job.id}"
            )
            req["session_source"] = "cron"

        run_id = str(uuid.uuid4())
        checkpoint_path: str | None = None
        checkpoint_summary: str | None = None

        # Auto-reset: checkpoint and create fresh session
        if job.runtime.auto_reset:
            old_session_id = req["session_id"]

            # Read current session messages for checkpoint
            baseline_messages = await read_session_messages(
                runner=self._runner,
                session_id=old_session_id,
                user_id=req["user_id"],
                channel=target_channel,
            )

            # Read compressed summary from session state
            compressed_summary = ""
            session = getattr(self._runner, "session", None)
            if session is not None:
                try:
                    state = await session.get_session_state_dict(
                        old_session_id,
                        req["user_id"],
                        target_channel,
                        allow_not_exist=True,
                    )
                    compressed_summary = (
                        state.get("agent", {})
                        .get("memory", {})
                        .get("_compressed_summary", "")
                    )
                except Exception:  # pylint: disable=broad-except
                    logger.warning(
                        "Failed to read compressed summary for checkpoint",
                    )

            # Save checkpoint if there are messages
            if baseline_messages or compressed_summary:
                checkpoint_path = _save_checkpoint(
                    checkpoint_dir=job.runtime.reset_checkpoint_dir,
                    job_id=job.id or "",
                    session_id=old_session_id,
                    messages=baseline_messages,
                    compressed_summary=compressed_summary,
                )
                checkpoint_summary = _build_checkpoint_summary(
                    baseline_messages,
                    compressed_summary,
                )

            # Create a fresh session_id with run_id
            new_session_id = f"cron:{job.id}:{run_id}"
            req["session_id"] = new_session_id
            req["session_source"] = "cron"

            # Inject checkpoint summary as prefix in the input
            if checkpoint_summary and req.get("input"):
                original_input = req["input"]
                if isinstance(original_input, str):
                    req[
                        "input"
                    ] = f"{checkpoint_summary}\n\n---\n\n{original_input}"
            elif checkpoint_summary:
                req["input"] = checkpoint_summary

            logger.info(
                "auto_reset: job_id=%s old_session=%s new_session=%s "
                "checkpoint=%s messages=%d",
                job.id,
                old_session_id,
                new_session_id,
                checkpoint_path,
                len(baseline_messages),
            )

        baseline_messages = await read_session_messages(
            runner=self._runner,
            session_id=req["session_id"],
            user_id=req["user_id"],
            channel=target_channel,
        )
        baseline_count = len(baseline_messages)

        await create_trace(
            run_id,
            meta={
                "job_id": job.id,
                "job_name": job.name,
                "task_type": "agent",
                "dispatch_channel": job.dispatch.channel,
                "target_user_id": target_user_id,
                "target_session_id": target_session_id,
                "auto_reset": job.runtime.auto_reset,
                "checkpoint_path": checkpoint_path,
            },
        )

        delivery_error: str | None = None

        async def _run() -> None:
            nonlocal delivery_error
            async for event in self._runner.stream_query(req):
                try:
                    await self._channel_manager.send_event(
                        channel=target_channel,
                        user_id=target_user_id,
                        session_id=target_session_id,
                        event=event,
                        meta=dispatch_meta,
                    )
                except Exception as e:  # pylint: disable=broad-except
                    if delivery_error is None:
                        delivery_error = repr(e)
                        logger.warning(
                            "cron agent delivery failed: job_id=%s "
                            "channel=%s error=%s",
                            job.id,
                            job.dispatch.channel,
                            delivery_error,
                        )

        try:
            await asyncio.wait_for(
                _run(),
                timeout=job.runtime.timeout_seconds,
            )
            await append_trace_from_session_delta(
                run_id=run_id,
                runner=self._runner,
                session_id=req["session_id"],
                user_id=req["user_id"],
                channel=target_channel,
                baseline_count=baseline_count,
            )
            await finalize_trace(run_id, status="success")
            return {
                "task_type": "agent",
                "run_id": run_id,
                "delivery_status": ("failed" if delivery_error else "success"),
                "delivery_error": delivery_error,
                "auto_reset": job.runtime.auto_reset,
                "checkpoint_path": checkpoint_path,
            }
        except asyncio.TimeoutError:
            logger.warning(
                "cron execute: job_id=%s timed out after %ss",
                job.id,
                job.runtime.timeout_seconds,
            )
            await append_trace_from_session_delta(
                run_id=run_id,
                runner=self._runner,
                session_id=req["session_id"],
                user_id=req["user_id"],
                channel=target_channel,
                baseline_count=baseline_count,
            )
            await finalize_trace(
                run_id,
                status="timeout",
                error=f"timed out after {job.runtime.timeout_seconds}s",
            )
            raise
        except asyncio.CancelledError:
            logger.info("cron execute: job_id=%s cancelled", job.id)
            await append_trace_from_session_delta(
                run_id=run_id,
                runner=self._runner,
                session_id=req["session_id"],
                user_id=req["user_id"],
                channel=target_channel,
                baseline_count=baseline_count,
            )
            await finalize_trace(
                run_id,
                status="cancelled",
                error="execution cancelled",
            )
            raise
        except Exception as e:  # pylint: disable=broad-except
            await append_trace_from_session_delta(
                run_id=run_id,
                runner=self._runner,
                session_id=req["session_id"],
                user_id=req["user_id"],
                channel=target_channel,
                baseline_count=baseline_count,
            )
            await finalize_trace(
                run_id,
                status="error",
                error=repr(e),
            )
            raise
