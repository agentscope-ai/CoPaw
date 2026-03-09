# -*- coding: utf-8 -*-

from copaw.app.channels.telegram.format_converter import (
    convert_markdown_to_telegram_html,
)


def test_convert_markdown_to_telegram_html_formats_code_block() -> None:
    text = "before ```print('hi')``` after"

    converted = convert_markdown_to_telegram_html(text)

    assert converted == "before \n<pre>print('hi')</pre>"


def test_convert_markdown_to_telegram_html_merges_blockquotes() -> None:
    text = "> first\n> second\nplain"

    converted = convert_markdown_to_telegram_html(text)

    assert converted == "<blockquote>first\nsecond</blockquote>\nplain"


def test_convert_markdown_to_telegram_html_bolds_table_headers() -> None:
    text = "| Col 1 | Col 2 |\n| --- | --- |\n| Val 1 | Val 2 |"

    converted = convert_markdown_to_telegram_html(text)

    assert converted == "<b>Col 1</b>\t<b>Col 2</b>\nVal 1\tVal 2"
