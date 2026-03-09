# -*- coding: utf-8 -*-

from copaw.app.channels.telegram.format_converter import (
    convert_markdown_to_telegram_html,
)


def test_convert_markdown_to_telegram_html_formats_code_block() -> None:
    text = "before ```print('hi')``` after"

    converted = convert_markdown_to_telegram_html(text)

    assert converted == "before \n<pre>print('hi')</pre>\n after"


def test_convert_markdown_to_telegram_html_merges_blockquotes() -> None:
    text = "> first\n> second\nplain"

    converted = convert_markdown_to_telegram_html(text)

    assert converted == "<blockquote>first\nsecond</blockquote>\nplain"


def test_convert_markdown_to_telegram_html_bolds_table_headers() -> None:
    text = "| Col 1 | Col 2 |\n| --- | --- |\n| Val 1 | Val 2 |"

    converted = convert_markdown_to_telegram_html(text)

    assert converted == "<b>Col 1</b>\t<b>Col 2</b>\nVal 1\tVal 2"


# Thread 28: HTML special chars in inline style content are escaped
def test_bold_content_with_html_special_chars_is_escaped() -> None:
    text = "**foo<bar>&baz**"

    converted = convert_markdown_to_telegram_html(text)

    assert converted == "<b>foo&lt;bar&gt;&amp;baz</b>"


def test_italic_content_with_html_special_chars_is_escaped() -> None:
    text = "*foo & <bar>*"

    converted = convert_markdown_to_telegram_html(text)

    assert converted == "<i>foo &amp; &lt;bar&gt;</i>"


def test_inline_code_content_is_escaped() -> None:
    text = "`foo<br>bar`"

    converted = convert_markdown_to_telegram_html(text)

    assert converted == "<code>foo&lt;br&gt;bar</code>"


def test_heading_title_is_html_escaped() -> None:
    text = "## Title with <b>raw tags</b>"

    converted = convert_markdown_to_telegram_html(text)

    assert converted == "<b>Title with &lt;b&gt;raw tags&lt;/b&gt;</b>"


# Thread 29: Table header bolding works when header cells contain HTML tags
def test_table_header_bolding_with_link_in_header() -> None:
    text = "| [Col](url) |\n| --- |\n| Val |"

    converted = convert_markdown_to_telegram_html(text)

    # The header cell contains an <a> tag; it should still be wrapped in <b>
    assert "<b>" in converted
    assert "<a href=" in converted


def test_table_header_single_column_already_bold_not_double_bolded() -> None:
    text = "| **Header** |\n| --- |\n| val |"

    converted = convert_markdown_to_telegram_html(text)

    # Cell rendered as <b>Header</b> should not become <b><b>Header</b></b>.
    assert "<b><b>" not in converted
