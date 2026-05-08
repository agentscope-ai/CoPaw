# -*- coding: utf-8 -*-
"""WeCom interactive template-card dispatcher.

This module is **routing-only** — it knows nothing about specific card
kinds.  Each card kind lives in its own module under :mod:`.` and is
registered into the dispatcher's lookup tables in :meth:`_register_kinds`.

Architecture
------------
Two lookup tables drive the dispatch:

* ``_by_message_type``    — outbound: matches an outgoing event's
  ``metadata.message_type`` to a ``render`` coroutine.
* ``_by_task_id_prefix``  — inbound: matches the ``task_id`` prefix of
  the clicked card to a ``handle`` coroutine.

Public entry-points called by :class:`~..channel.WecomChannel`:
:meth:`try_send_card_for_event` and :meth:`handle_template_card_event_sync`.

Adding a new card kind: drop a module under :mod:`.` exposing module-
level metadata (``NAME`` / ``MESSAGE_TYPE`` / ``TASK_ID_PREFIX``) and
two coroutines (``render`` / ``handle``), then register it in
:meth:`_register_kinds`.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Optional,
)

from . import context

if TYPE_CHECKING:
    from ..channel import WecomChannel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Registry record
# ---------------------------------------------------------------------

# Outbound: given (channel, to_handle, event, send_meta, meta) build +
# send the card.  Returns True if the card was sent so the caller can
# skip the default text rendering.
RenderFn = Callable[
    ["WecomChannel", str, Any, Dict[str, Any], Dict[str, Any]],
    Awaitable[bool],
]

# Inbound: given (channel, raw WeCom callback frame), perform the card
# update and any side effects (queue injection, etc).
HandleFn = Callable[["WecomChannel", Any], Awaitable[None]]


@dataclass(frozen=True)
class CardKind:
    """Describes one kind of template card and its handlers."""

    name: str  # human-readable tag for logs
    message_type: str  # matches ``metadata.message_type`` (outbound)
    task_id_prefix: str  # matches ``task_id`` prefix (inbound)
    render: RenderFn
    handle: HandleFn


# ---------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------


class WecomCardHandler:
    """Routing-only dispatcher for WeCom interactive template cards."""

    def __init__(self, channel: "WecomChannel") -> None:
        self._channel = channel
        self._by_message_type: Dict[str, CardKind] = {}
        self._by_task_id_prefix: Dict[str, CardKind] = {}
        self._register_kinds()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, kind: CardKind) -> None:
        """Install a card kind into both lookup tables."""
        if kind.message_type in self._by_message_type:
            logger.warning(
                "wecom card: message_type %r already registered, overriding",
                kind.message_type,
            )
        if kind.task_id_prefix in self._by_task_id_prefix:
            logger.warning(
                "wecom card: task_id_prefix %r already registered, "
                "overriding",
                kind.task_id_prefix,
            )
        self._by_message_type[kind.message_type] = kind
        self._by_task_id_prefix[kind.task_id_prefix] = kind

    def _register_kinds(self) -> None:
        """Register every built-in card kind.

        Each card module exposes module-level metadata
        (``NAME`` / ``MESSAGE_TYPE`` / ``TASK_ID_PREFIX``) and two
        coroutines (``render(channel, ...)`` / ``handle(channel, frame)``).
        We wrap them in a :class:`CardKind` here so the dispatch wiring
        stays in one place.

        Adding a new card kind: drop a module exposing the metadata and
        coroutines, then add one block below.
        """
        from . import tool_guard

        self.register(
            CardKind(
                name=tool_guard.NAME,
                message_type=tool_guard.MESSAGE_TYPE,
                task_id_prefix=tool_guard.TASK_ID_PREFIX,
                render=tool_guard.render,
                handle=tool_guard.handle,
            ),
        )

    # ==================================================================
    # Public entry-points (called by WecomChannel)
    # ==================================================================

    async def try_send_card_for_event(
        self,
        to_handle: str,
        event: Any,
        send_meta: Dict[str, Any],
    ) -> bool:
        """Render ``event`` as a template card if any kind matches.

        Returns ``True`` when a card was sent (the caller should then
        skip the default text rendering), ``False`` otherwise.
        """
        meta = context.extract_meta(event)
        if meta is None:
            return False
        kind = self._by_message_type.get(str(meta.get("message_type") or ""))
        if kind is None:
            return False
        try:
            return await kind.render(
                self._channel, to_handle, event, send_meta, meta,
            )
        except Exception:
            logger.exception(
                "wecom card render failed: kind=%s",
                kind.name,
            )
            return False

    def handle_template_card_event_sync(self, frame: Any) -> None:
        """Sync entry called from the WS thread on a card event.

        Routes by ``task_id`` prefix to the registered handler and
        dispatches to the main event loop for async processing.
        """
        loop = self._channel._loop  # noqa: SLF001
        if not loop or not loop.is_running():
            logger.warning(
                "wecom card event: main loop not running, drop event",
            )
            return

        kind = self._lookup_kind_for_frame(frame)
        if kind is None:
            # Not a recognised card event; ignore silently.
            return

        asyncio.run_coroutine_threadsafe(
            self._safe_handle(kind, frame),
            loop,
        )

    async def _safe_handle(
        self,
        kind: CardKind,
        frame: Any,
    ) -> None:
        """Wrap the registered handler with logging."""
        try:
            await kind.handle(self._channel, frame)
        except Exception:
            logger.exception(
                "wecom card handle failed: kind=%s",
                kind.name,
            )

    def _lookup_kind_for_frame(self, frame: Any) -> Optional[CardKind]:
        """Find the CardKind matching the frame's ``task_id`` prefix."""
        body = frame.get("body") or {} if isinstance(frame, dict) else {}
        event = body.get("event") or {}
        tce = event.get("template_card_event") or event
        task_id = str(tce.get("task_id") or "")
        if not task_id:
            return None
        for prefix, kind in self._by_task_id_prefix.items():
            if task_id.startswith(prefix):
                return kind
        return None


__all__ = ["WecomCardHandler", "CardKind"]
