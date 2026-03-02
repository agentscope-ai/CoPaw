# -*- coding: utf-8 -*-

import locale

from copaw.agents.tools.shell import _decode_output_bytes


def test_decode_output_bytes_prefers_utf8() -> None:
    data = "中文输出".encode("utf-8")
    assert _decode_output_bytes(data) == "中文输出"


def test_decode_output_bytes_falls_back_to_preferred_encoding(
    monkeypatch,
) -> None:
    monkeypatch.setattr(locale, "getpreferredencoding", lambda _: "gb18030")
    text = "中文输出"
    data = text.encode("gb18030")
    assert _decode_output_bytes(data) == text
