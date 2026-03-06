# -*- coding: utf-8 -*-
"""
Telegram Format Converter V2
Converts standard Markdown to Telegram HTML format

Conversion rules:
- Headings (# ## ### ####) → <b>heading</b>
- Bold **text** → <b>text</b>
- Italic *text* → <i>text</i>
- Strikethrough ~~text~~ → <s>text</s>
- Inline code `code` → <code>code</code>
- Code blocks ```code``` → <pre>code</pre>
- Blockquotes > text → <blockquote>text</blockquote> (multi-line merged)
- Tables |col1|col2| → col1\tcol2 (header bolded)
- Lists - item → • item
- Separators --- → ──────────
- Links [text](url) → <a href="url">text</a>
"""

import re
import logging

logger = logging.getLogger(__name__)


def convert_markdown_to_telegram_html(text: str) -> str:
    """
    Convert Markdown format to Telegram HTML format

    Args:
        text: Text in Markdown format

    Returns:
        Text in Telegram HTML format
    """
    if not text:
        return text

    logger.debug(f"[FORMAT] Input: {mask_text(text, 100)}")

    lines = text.split("\n")
    converted_lines = []

    # State tracking
    in_code_block = False
    code_block_content = []
    in_blockquote = False
    blockquote_lines = []
    table_header_pending = False

    def flush_blockquote():
        """Flush blockquote content"""
        nonlocal in_blockquote, blockquote_lines
        if in_blockquote and blockquote_lines:
            joined = "\n".join(blockquote_lines)
            converted_lines.append(f"<blockquote>{joined}</blockquote>")
            blockquote_lines = []
            in_blockquote = False

    def flush_code_block():
        """Flush code block content"""
        nonlocal in_code_block, code_block_content
        if code_block_content:
            code_text = "\n".join(code_block_content)
            code_text = escape_html(code_text)
            converted_lines.append(f"<pre>{code_text}</pre>")
        # Always reset state, even for empty blocks
        code_block_content = []
        in_code_block = False

    def process_table_header():
        """Process pending table header (bold)"""
        nonlocal table_header_pending
        if table_header_pending and converted_lines:
            prev = converted_lines[-1]
            if not prev.startswith("<"):
                # Support single-column tables (no tabs)
                if "\t" in prev:
                    cells = prev.split("\t")
                    converted_lines[-1] = "\t".join(f"<b>{cell}</b>" for cell in cells)
                else:
                    # Single column case
                    converted_lines[-1] = f"<b>{prev}</b>"
        table_header_pending = False

    for line in lines:
        # 1. Code block detection (detect ``` anywhere in line)
        if "```" in line:
            if in_code_block:
                # Inside code block, ``` indicates end
                code_line = line.split("```")[0]
                if code_line:
                    code_block_content.append(code_line)
                flush_code_block()
                # Process content after ``` (if any)
                parts = line.split("```", 1)
                if len(parts) > 1 and parts[1].strip():
                    # Content after end on same line, continue processing without re-entering code block
                    line = parts[1]
                    # Fall through to process the remaining content
                else:
                    continue
            else:
                # Not in code block, ``` indicates start
                flush_blockquote()
                process_table_header()
                # Process content before ``` normally (add as processed line)
                before = line.split("```")[0]
                if before.strip():
                    # Process inline styles in content before ```
                    processed_before = before
                    # Strikethrough
                    if "~~" in processed_before:
                        processed_before = re.sub(
                            r"~~(.+?)~~",
                            r"<s>\1</s>",
                            processed_before,
                        )
                    # Bold
                    if "**" in processed_before:
                        processed_before = re.sub(
                            r"\*\*(.+?)\*\*",
                            r"<b>\1</b>",
                            processed_before,
                        )
                    # Italic
                    processed_before = re.sub(
                        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
                        r"<i>\1</i>",
                        processed_before,
                    )
                    # Inline code
                    if "`" in processed_before:
                        processed_before = re.sub(
                            r"`(.+?)`",
                            r"<code>\1</code>",
                            processed_before,
                        )

                    # Link
                    def _replace_link_v1(match):
                        text = escape_html(match.group(1))
                        href = escape_html(match.group(2), quote=True)
                        return f'<a href="{href}">{text}</a>'

                    if re.search(r"\[.+?\]\(.+?\)", processed_before):
                        processed_before = re.sub(
                            r"\[(.+?)\]\((.+?)\)",
                            _replace_link_v1,
                            processed_before,
                        )
                    converted_lines.append(processed_before)

                # Check if there is content after ``` (same line, single-line code block)
                after_parts = line.split("```")[1:]
                if len(after_parts) >= 2 and after_parts[0].strip():
                    # Single line has start and end (```code``` format)
                    code_content = after_parts[0]
                    if code_content.strip():
                        # Process single-line code block directly, do not set state
                        code_text = escape_html(code_content)
                        converted_lines.append(f"<pre>{code_text}</pre>")
                    # Process content after the last ```
                    if len(after_parts) > 2 and after_parts[2].strip():
                        line = after_parts[2]
                    else:
                        continue
                else:
                    # Standard code block start
                    in_code_block = True
                    continue

        if in_code_block:
            code_block_content.append(line)
            continue

        # 2. Title processing (support anywhere in line, e.g., "[TG_bot]  ## Title")
        title_match = re.search(r"(######?|#####|####|###|##|#)\s+(.+)", line)
        if title_match:
            flush_blockquote()
            process_table_header()
            prefix = line[: title_match.start()].strip()
            title = title_match.group(2).strip()
            if prefix:
                converted_lines.append(f"{prefix} <b>{title}</b>")
            else:
                converted_lines.append(f"<b>{title}</b>")
            continue

        # 3. Horizontal separator
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", line.strip()):
            flush_blockquote()
            process_table_header()
            converted_lines.append("──────────")
            continue

        # 4. Table detection
        if re.match(r"^\|.*\|$", line.strip()):
            flush_blockquote()
            # Check if it is a separator row (|---|---|)
            if re.match(r"^\|[\s\-:|]+\|$", line.strip()):
                table_header_pending = True
                continue

            # Data row
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if cells:
                process_table_header()
                # Process inline styles for each cell
                processed_cells = []
                for cell in cells:
                    cell_line = cell
                    # Strikethrough
                    if "~~" in cell_line:
                        cell_line = re.sub(
                            r"~~(.+?)~~",
                            r"<s>\1</s>",
                            cell_line,
                        )
                    # Bold
                    if "**" in cell_line:
                        cell_line = re.sub(
                            r"\*\*(.+?)\*\*",
                            r"<b>\1</b>",
                            cell_line,
                        )
                    if "__" in cell_line:
                        cell_line = re.sub(
                            r"__(.+?)__",
                            r"<b>\1</b>",
                            cell_line,
                        )
                    # Italic
                    cell_line = re.sub(
                        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
                        r"<i>\1</i>",
                        cell_line,
                    )
                    cell_line = re.sub(
                        r"(?<![a-zA-Z0-9_])_(.+?)_(?![a-zA-Z0-9_])",
                        r"<i>\1</i>",
                        cell_line,
                    )
                    # Inline code
                    if "`" in cell_line:
                        cell_line = re.sub(
                            r"`(.+?)`",
                            r"<code>\1</code>",
                            cell_line,
                        )

                    # Link
                    def _replace_link_v2(match):
                        text = escape_html(match.group(1))
                        href = escape_html(match.group(2), quote=True)
                        return f'<a href="{href}">{text}</a>'

                    if re.search(r"\[.+?\]\(.+?\)", cell_line):
                        cell_line = re.sub(
                            r"\[(.+?)\]\((.+?)\)",
                            _replace_link_v2,
                            cell_line,
                        )
                    processed_cells.append(cell_line)
                converted_lines.append("\t".join(processed_cells))
            continue

        # 5. Blockquote processing (supports multi-line merge)
        if line.startswith("> "):
            if not in_blockquote:
                in_blockquote = True
                blockquote_lines = [line[2:].strip()]
            else:
                blockquote_lines.append(line[2:].strip())
            continue
        else:
            flush_blockquote()

        # 6. List prefix replacement
        if re.match(r"^[-*+]\s+", line):
            line = re.sub(r"^[-*+]\s+", "• ", line)

        # 7. Inline style processing (order matters!)
        # 7.1 Strikethrough
        if "~~" in line:
            line = re.sub(r"~~(.+?)~~", r"<s>\1</s>", line)

        # 7.2 Bold
        if "**" in line:
            line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        if "__" in line:
            line = re.sub(r"__(.+?)__", r"<b>\1</b>", line)

        # 7.3 Italic (after Bold to avoid conflicts)
        line = re.sub(
            r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
            r"<i>\1</i>",
            line,
        )
        line = re.sub(
            r"(?<![a-zA-Z0-9_])_(.+?)_(?![a-zA-Z0-9_])",
            r"<i>\1</i>",
            line,
        )

        # 7.4 Inline code
        if "`" in line:
            line = re.sub(r"`(.+?)`", r"<code>\1</code>", line)

        # 7.5 Link
        def _replace_link_v3(match):
            text = escape_html(match.group(1))
            href = escape_html(match.group(2), quote=True)
            return f'<a href="{href}">{text}</a>'

        if re.search(r"\[.+?\]\(.+?\)", line):
            line = re.sub(r"\[(.+?)\]\((.+?)\)", _replace_link_v3, line)

        converted_lines.append(line)

    # Flush remaining content
    flush_blockquote()
    flush_code_block()
    process_table_header()

    result = "\n".join(converted_lines)
    logger.debug(f"[FORMAT] Output: {mask_text(result, 100)}")
    return result


def escape_html(text: str, quote: bool = False) -> str:
    """
    HTML escape

    Args:
        text: Original text
        quote: Whether to escape quotes (for attribute values)

    Returns:
        Escaped text
    """
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    if quote:
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")
    return text


def mask_text(text: str, max_length: int = 50) -> str:
    """
    Mask text for logging

    Args:
        text: Original text
        max_length: Maximum display length

    Returns:
        Masked text
    """
    if not text:
        return "<empty>"
    length = len(text)
    snippet = text[:max_length].replace("\n", "\\n").replace("\r", "\\r")
    if length > max_length:
        return f"<{length} chars: {snippet}...>"
    return f"<{length} chars: {snippet}>"


if __name__ == "__main__":
    test_text = """# Main Heading

## Secondary Heading

### Sub Heading

This is a test for **bold** and *italic*

- List item one
- List item two
- List item three

1. Ordered list one
2. Ordered list two

> This is blockquote content
> Second line quote
> Third line quote

```python
def hello():
    print("Hello")
```

| Col 1 | Col 2 |
|------|------|
| Val 1 | Val 2 |
| Val 3 | Val 4 |

[Link Text](https://example.com)

~~Strikethrough~~

---

Plain text
"""

    result = convert_markdown_to_telegram_html(test_text)
    print("Conversion Result:")
    print("=" * 60)
    print(result)
    print("=" * 60)
    print("\nVerification:")
    print("✓ Bold:", "<b>" in result)
    print("✓ Italic:", "<i>" in result)
    print("✓ Heading:", "<b>Main Heading</b>" in result)
    print("✓ List:", "• " in result)
    print("✓ Blockquote:", "<blockquote>" in result and "\n" in result)
    print("✓ Table tabs:", "\t" in result)
    print("✓ Table header bold:", "<b>Col 1</b>" in result)
    print("✓ Code block:", "<pre>" in result)
    print("✓ Link:", "<a href=" in result)
    print("✓ Strikethrough:", "<s>" in result)
    print("✓ Separator:", "──────────" in result)
