# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from datetime import datetime
import logging
import uuid
from typing import Any, Dict

from ..inbox_trace_store import (
    append_trace_event,
    create_trace,
    finalize_trace,
)
from .models import CronJobSpec

logger = logging.getLogger(__name__)


class CronExecutor:
    def __init__(self, *, runner: Any, channel_manager: Any):
        self._runner = runner
        self._channel_manager = channel_manager

    @staticmethod
    def _flatten_session_messages(content: Any) -> list[dict[str, Any]]:
        if not isinstance(content, list):
            return []
        messages: list[dict[str, Any]] = []
        for item in content:
            if isinstance(item, dict):
                messages.append(item)
                continue
            if isinstance(item, list) and item and isinstance(item[0], dict):
                messages.append(item[0])
        return messages

    @staticmethod
    def _parse_session_timestamp(value: Any) -> float | None:
        if not isinstance(value, str) or not value.strip():
            return None
        raw = value.strip()
        formats = ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S")
        for fmt in formats:
            try:
                dt = datetime.strptime(raw, fmt)
                return dt.timestamp()
            except ValueError:
                continue
        return None

    async def _read_session_messages(
        self,
        *,
        session_id: str,
        user_id: str,
        channel: str,
    ) -> list[dict[str, Any]]:
        session = getattr(self._runner, "session", None)
        if session is None:
            return []
        try:
            state = await session.get_session_state_dict(
                session_id,
                user_id,
                channel,
                allow_not_exist=True,
            )
        except Exception:  # pylint: disable=broad-except
            return []
        memory = state.get("agent", {}).get("memory", {})
        return self._flatten_session_messages(memory.get("content"))

    async def _append_trace_from_session_delta(
        self,
        *,
        run_id: str,
        session_id: str,
        user_id: str,
        channel: str,
        baseline_count: int,
    ) -> None:
        messages = await self._read_session_messages(
            session_id=session_id,
            user_id=user_id,
            channel=channel,
        )
        baseline_count = max(baseline_count, 0)
        for msg in messages[baseline_count:]:
            at = self._parse_session_timestamp(msg.get("timestamp"))
            await append_trace_event(run_id, msg, at=at)

    # pylint: disable=too-many-statements
    async def execute(self, job: CronJobSpec) -> dict[str, Any]:
        """Execute one job once.

        - task_type text: send fixed text to channel
        - task_type agent: ask agent with prompt, send reply to channel (
            stream_query + send_event)
        """
        target_user_id = job.dispatch.target.user_id
        target_session_id = job.dispatch.target.session_id
        target_channel = job.dispatch.channel
        dispatch_meta: Dict[str, Any] = dict(job.dispatch.meta or {})
        logger.info(
            "cron execute: job_id=%s channel=%s task_type=%s "
            "target_user_id=%s target_session_id=%s",
            job.id,
            target_channel,
            job.task_type,
            target_user_id[:40] if target_user_id else "",
            target_session_id[:40] if target_session_id else "",
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
            req["session_id"] = (
                f"{target_session_id}:cron:{job.id}"
                if target_session_id
                else f"cron:{job.id}"
            )
        run_id = str(uuid.uuid4())
        delivery_error: str | None = None
        baseline_messages = await self._read_session_messages(
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
            },
        )

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
            await self._append_trace_from_session_delta(
                run_id=run_id,
                session_id=req["session_id"],
                user_id=req["user_id"],
                channel=target_channel,
                baseline_count=baseline_count,
            )
            await finalize_trace(run_id, status="success")
            return {
                "task_type": "agent",
                "run_id": run_id,
                "delivery_status": "failed" if delivery_error else "success",
                "delivery_error": delivery_error,
            }
        except asyncio.TimeoutError:
            logger.warning(
                "cron execute: job_id=%s timed out after %ss",
                job.id,
                job.runtime.timeout_seconds,
            )
            await self._append_trace_from_session_delta(
                run_id=run_id,
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
            await self._append_trace_from_session_delta(
                run_id=run_id,
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
            await self._append_trace_from_session_delta(
                run_id=run_id,
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
