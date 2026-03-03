# -*- coding: utf-8 -*-
import pytest

from copaw.agents.tools.send_file import send_file_to_user


@pytest.mark.asyncio
async def test_send_file_to_user_not_emit_fake_success_text(tmp_path) -> None:
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(b"copaw")

    response = await send_file_to_user(str(file_path))

    assert response.content
    assert all(
        not (
            getattr(block, "type", None) == "text"
            and getattr(block, "text", "") == "已成功发送文件"
        )
        for block in response.content
    )
