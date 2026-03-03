from __future__ import annotations

import sys
import types
from typing import Any, AsyncIterator


async def _dummy_process(_: Any) -> AsyncIterator[Any]:
    if False:
        yield None


def _install_agentscope_runtime_stub() -> None:
    if "agentscope_runtime.engine.schemas.agent_schemas" in sys.modules:
        return

    runtime_module = types.ModuleType("agentscope_runtime")
    engine_module = types.ModuleType("agentscope_runtime.engine")
    schemas_module = types.ModuleType("agentscope_runtime.engine.schemas")
    agent_schemas_module = types.ModuleType(
        "agentscope_runtime.engine.schemas.agent_schemas",
    )

    class _RunStatus:
        Completed = "completed"

    class _MessageType:
        MESSAGE = "message"

    class _ContentType:
        TEXT = "text"
        IMAGE = "image"
        VIDEO = "video"
        AUDIO = "audio"
        FILE = "file"
        REFUSAL = "refusal"

    class _BaseContent:
        def __init__(self, type: str, **kwargs: Any):
            self.type = type
            for k, v in kwargs.items():
                setattr(self, k, v)

    class TextContent(_BaseContent):
        pass

    class ImageContent(_BaseContent):
        pass

    class VideoContent(_BaseContent):
        pass

    class AudioContent(_BaseContent):
        pass

    class FileContent(_BaseContent):
        pass

    class RefusalContent(_BaseContent):
        pass

    agent_schemas_module.RunStatus = _RunStatus
    agent_schemas_module.MessageType = _MessageType
    agent_schemas_module.ContentType = _ContentType
    agent_schemas_module.TextContent = TextContent
    agent_schemas_module.ImageContent = ImageContent
    agent_schemas_module.VideoContent = VideoContent
    agent_schemas_module.AudioContent = AudioContent
    agent_schemas_module.FileContent = FileContent
    agent_schemas_module.RefusalContent = RefusalContent

    sys.modules["agentscope_runtime"] = runtime_module
    sys.modules["agentscope_runtime.engine"] = engine_module
    sys.modules["agentscope_runtime.engine.schemas"] = schemas_module
    sys.modules[
        "agentscope_runtime.engine.schemas.agent_schemas"
    ] = agent_schemas_module


def _build_channel(bot_prefix: str) -> Any:
    _install_agentscope_runtime_stub()
    from copaw.app.channels.imessage.channel import IMessageChannel

    return IMessageChannel(
        process=_dummy_process,
        enabled=True,
        db_path="~/Library/Messages/chat.db",
        poll_sec=1.0,
        bot_prefix=bot_prefix,
    )


def test_should_skip_empty_message() -> None:
    channel = _build_channel("@bot")
    assert channel._should_skip_incoming_text("")
    assert channel._should_skip_incoming_text(None)


def test_should_skip_message_without_prefix_when_prefix_configured() -> None:
    channel = _build_channel("@bot")
    assert channel._should_skip_incoming_text("hello")


def test_should_accept_message_with_prefix_when_prefix_configured() -> None:
    channel = _build_channel("@bot")
    assert not channel._should_skip_incoming_text("@bot hello")


def test_should_accept_any_non_empty_message_when_prefix_empty() -> None:
    channel = _build_channel("")
    assert not channel._should_skip_incoming_text("hello")
