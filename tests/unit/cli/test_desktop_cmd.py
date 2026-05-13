# -*- coding: utf-8 -*-
from qwenpaw.cli.desktop_cmd import WebViewAPI


def test_open_external_link_allows_file_urls(monkeypatch):
    opened = []
    monkeypatch.setattr(
        "qwenpaw.cli.desktop_cmd.webbrowser.open",
        opened.append,
    )

    WebViewAPI().open_external_link("file:///Users/test/token.txt")

    assert opened == ["file:///Users/test/token.txt"]


def test_open_external_link_rejects_script_urls(monkeypatch):
    opened = []
    monkeypatch.setattr(
        "qwenpaw.cli.desktop_cmd.webbrowser.open",
        opened.append,
    )

    WebViewAPI().open_external_link("javascript:alert(1)")

    assert not opened
