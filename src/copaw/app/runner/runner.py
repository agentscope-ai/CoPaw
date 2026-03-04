# -*- coding: utf-8 -*-
# pylint: disable=unused-argument too-many-branches too-many-statements
import asyncio
import json
import logging
import os
from pathlib import Path

from agentscope.pipeline import stream_printing_messages
from agentscope.tool import Toolkit
from agentscope_runtime.engine.runner import Runner
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from dotenv import load_dotenv

from .command_dispatch import (
    _get_last_user_text,
    _is_command,
    run_command_path,
)
from .query_error_dump import write_query_error_dump
from .session import SafeJSONSession
from .utils import build_env_context
from ..channels.schema import DEFAULT_CHANNEL
from ...agents.memory import MemoryManager
from ...agents.model_factory import create_model_and_formatter
from ...agents.react_agent import CoPawAgent
from ...agents.tools import read_file, write_file, edit_file
from ...agents.utils.token_counting import _get_token_counter
from ...config import load_config
from ...constant import (
    MEMORY_COMPACT_RATIO,
    WORKING_DIR,
)

logger = logging.getLogger(__name__)


class AgentRunner(Runner):
    def __init__(self) -> None:
        super().__init__()
        self.framework_type = "agentscope"
        self._chat_manager = None  # Store chat_manager reference
        self._mcp_manager = None  # MCP client manager for hot-reload
        self.memory_manager: MemoryManager | None = None

    def set_chat_manager(self, chat_manager):
        """Set chat manager for auto-registration.

        Args:
            chat_manager: ChatManager instance
        """
        self._chat_manager = chat_manager

    def set_mcp_manager(self, mcp_manager):
        """Set MCP client manager for hot-reload support.

        Args:
            mcp_manager: MCPClientManager instance
        """
        self._mcp_manager = mcp_manager

    # -- Session overflow protection ----------------------------------------

    # Maximum session file size in bytes before emergency truncation.
    _SESSION_FILE_SIZE_LIMIT: int = 2 * 1024 * 1024  # 2 MB

    # Number of recent messages to keep when truncating.
    _SESSION_KEEP_RECENT: int = 5

    async def _guard_session_overflow(
        self,
        agent: CoPawAgent,
        session_id: str,
        user_id: str,
    ) -> None:
        """Truncate agent memory if the session file is dangerously large.

        This is a hard guard that does NOT require an LLM call – it simply
        drops old messages and keeps only the most recent ones.  It fires
        *before* the model is called, so that we never send a prompt that
        exceeds the model's context window.

        Args:
            agent: The CoPawAgent whose memory may be truncated.
            session_id: Current session id (for logging / file lookup).
            user_id: Current user id (for file lookup).
        """
        try:
            session_path = self.session._get_save_path(session_id, user_id)
            if not os.path.exists(session_path):
                return

            file_size = os.path.getsize(session_path)
            if file_size < self._SESSION_FILE_SIZE_LIMIT:
                return

            # --- Emergency truncation ---
            total_msgs = len(agent.memory.content)
            keep = self._SESSION_KEEP_RECENT

            if total_msgs <= keep:
                logger.warning(
                    "Session file is large (%d bytes, %d messages) but "
                    "too few messages to truncate – skipping.",
                    file_size,
                    total_msgs,
                )
                return

            removed = total_msgs - keep
            agent.memory.content = agent.memory.content[-keep:]
            # Clear the compressed summary (it refers to now-deleted msgs)
            agent.memory._compressed_summary = ""

            logger.warning(
                "Session overflow protection: truncated %d messages "
                "(kept last %d). File was %d bytes (%s).",
                removed,
                keep,
                file_size,
                session_path,
            )
        except Exception as exc:
            logger.error(
                "Session overflow guard failed: %s",
                exc,
                exc_info=True,
            )

    @staticmethod
    def _is_prompt_too_long(exc: Exception) -> bool:
        """Return True if *exc* indicates the prompt exceeded the model
        context limit."""
        msg = str(exc).lower()
        return "prompt is too long" in msg or "prompt_too_long" in msg

    # -----------------------------------------------------------------------

    async def query_handler(
        self,
        msgs,
        request: AgentRequest = None,
        **kwargs,
    ):
        """
        Handle agent query.
        """
        # Command path: do not create agent; yield from run_command_path
        query = _get_last_user_text(msgs)
        if query and _is_command(query):
            logger.info("Command path: %s", query.strip()[:50])
            async for msg, last in run_command_path(request, msgs, self):
                yield msg, last
            return

        agent = None
        chat = None
        session_state_loaded = False
        try:
            session_id = request.session_id
            user_id = request.user_id
            channel = getattr(request, "channel", DEFAULT_CHANNEL)

            logger.info(
                "Handle agent query:\n%s",
                json.dumps(
                    {
                        "session_id": session_id,
                        "user_id": user_id,
                        "channel": channel,
                        "msgs_len": len(msgs) if msgs else 0,
                        "msgs_str": str(msgs)[:300] + "...",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            env_context = build_env_context(
                session_id=session_id,
                user_id=user_id,
                channel=channel,
                working_dir=str(WORKING_DIR),
            )

            # Get MCP clients from manager (hot-reloadable)
            mcp_clients = []
            if self._mcp_manager is not None:
                mcp_clients = await self._mcp_manager.get_clients()

            config = load_config()
            max_iters = config.agents.running.max_iters
            max_input_length = config.agents.running.max_input_length

            agent = CoPawAgent(
                env_context=env_context,
                mcp_clients=mcp_clients,
                memory_manager=self.memory_manager,
                max_iters=max_iters,
                max_input_length=max_input_length,
            )
            await agent.register_mcp_clients()
            agent.set_console_output_enabled(enabled=False)

            logger.debug(
                f"Agent Query msgs {msgs}",
            )

            name = "New Chat"
            if len(msgs) > 0:
                content = msgs[0].get_text_content()
                if content:
                    name = msgs[0].get_text_content()[:10]
                else:
                    name = "Media Message"

            if self._chat_manager is not None:
                chat = await self._chat_manager.get_or_create_chat(
                    session_id,
                    user_id,
                    channel,
                    name=name,
                )

            try:
                await self.session.load_session_state(
                    session_id=session_id,
                    user_id=user_id,
                    agent=agent,
                )
            except KeyError as e:
                logger.warning(
                    "load_session_state skipped (state schema mismatch): %s; "
                    "will save fresh state on completion to recover file",
                    e,
                )
            session_state_loaded = True

            # --- Layer 1: proactive session overflow guard ---
            await self._guard_session_overflow(agent, session_id, user_id)

            # Rebuild system prompt so it always reflects the latest
            # AGENTS.md / SOUL.md / PROFILE.md, not the stale one saved
            # in the session state.
            agent.rebuild_sys_prompt()

            async for msg, last in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(msgs),
            ):
                yield msg, last

        except asyncio.CancelledError as exc:
            logger.info(f"query_handler: {session_id} cancelled!")
            if agent is not None:
                await agent.interrupt()
            raise RuntimeError("Task has been cancelled!") from exc
        except Exception as e:
            # --- Layer 2: catch prompt-too-long and retry once ---
            if self._is_prompt_too_long(e) and agent is not None:
                logger.warning(
                    "Prompt too long detected – clearing session and "
                    "retrying once. Original error: %s",
                    e,
                )
                try:
                    # Wipe all memory and retry
                    agent.memory.content = []
                    agent.memory._compressed_summary = ""
                    agent.rebuild_sys_prompt()

                    async for msg, last in stream_printing_messages(
                        agents=[agent],
                        coroutine_task=agent(msgs),
                    ):
                        yield msg, last
                    # Retry succeeded – skip the original raise
                    return
                except Exception as retry_exc:
                    logger.exception(
                        "Retry after session clear also failed: %s",
                        retry_exc,
                    )
                    e = retry_exc  # fall through to normal error path

            debug_dump_path = write_query_error_dump(
                request=request,
                exc=e,
                locals_=locals(),
            )
            path_hint = (
                f"\n(Details:  {debug_dump_path})" if debug_dump_path else ""
            )
            logger.exception(f"Error in query handler: {e}{path_hint}")
            if debug_dump_path:
                setattr(e, "debug_dump_path", debug_dump_path)
                if hasattr(e, "add_note"):
                    e.add_note(
                        f"(Details:  {debug_dump_path})",
                    )
                suffix = f"\n(Details:  {debug_dump_path})"
                e.args = (
                    (f"{e.args[0]}{suffix}" if e.args else suffix.strip()),
                ) + e.args[1:]
            raise
        finally:
            if agent is not None and session_state_loaded:
                await self.session.save_session_state(
                    session_id=session_id,
                    user_id=user_id,
                    agent=agent,
                )

            if self._chat_manager is not None and chat is not None:
                await self._chat_manager.update_chat(chat)

    async def init_handler(self, *args, **kwargs):
        """
        Init handler.
        """
        # Load environment variables from .env file
        env_path = Path(__file__).resolve().parents[4] / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug(f"Loaded environment variables from {env_path}")
        else:
            logger.debug(
                f".env file not found at {env_path}, "
                "using existing environment variables",
            )

        session_dir = str(WORKING_DIR / "sessions")
        self.session = SafeJSONSession(save_dir=session_dir)

        try:
            if self.memory_manager is None:
                # Get config for memory manager
                config = load_config()
                max_input_length = config.agents.running.max_input_length

                # Create model and formatter
                chat_model, formatter = create_model_and_formatter()

                # Get token counter
                token_counter = _get_token_counter()

                # Create toolkit for memory manager
                toolkit = Toolkit()
                toolkit.register_tool_function(read_file)
                toolkit.register_tool_function(write_file)
                toolkit.register_tool_function(edit_file)

                # Initialize MemoryManager with new parameters
                self.memory_manager = MemoryManager(
                    working_dir=str(WORKING_DIR),
                    chat_model=chat_model,
                    formatter=formatter,
                    token_counter=token_counter,
                    toolkit=toolkit,
                    max_input_length=max_input_length,
                    memory_compact_ratio=MEMORY_COMPACT_RATIO,
                )
            await self.memory_manager.start()
        except Exception as e:
            logger.exception(f"MemoryManager start failed: {e}")

    async def shutdown_handler(self, *args, **kwargs):
        """
        Shutdown handler.
        """
        try:
            await self.memory_manager.close()
        except Exception as e:
            logger.warning(f"MemoryManager stop failed: {e}")
