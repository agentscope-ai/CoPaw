# -*- coding: utf-8 -*-
"""Patch channel.py: start from upstream clean version, apply only our changes.

Changes:
1. Add _DISCORD_MAX_LEN constant
2. Add _chunk_text() static method with code-fence awareness
3. Modify send() to use chunking
"""
import subprocess
import re


def main():
    # Read upstream clean version
    result = subprocess.run(
        ["git", "show",
         "upstream/main:src/copaw/app/channels/discord_/channel.py"],
        capture_output=True,
    )
    code = result.stdout.decode("utf-8")
    lines = code.split("\n")

    # ---- Patch 1: Add _DISCORD_MAX_LEN after 'uses_manager_queue' ----
    for i, line in enumerate(lines):
        if "uses_manager_queue = True" in line:
            lines.insert(i + 1, "    _DISCORD_MAX_LEN: int = 2000")
            break

    # ---- Patch 2: Add _chunk_text method before 'async def send(' ----
    fence = "``" + "`"  # avoid triple-backtick in source
    tilde_fence = "~~" + "~"
    chunk_text_lines = [
        "    @staticmethod",
        "    def _chunk_text(text: str, max_len: int = 2000) -> list[str]:",
        '        """Split *text* into chunks that fit Discord\'s message limit.',
        "",
        "        Splits at newline boundaries to preserve formatting.  If a single",
        "        line exceeds *max_len* it is hard-split at *max_len*.",
        "",
        f"        Code fences ({fence}) are tracked so that a chunk ending inside",
        "        an open fence gets a closing fence appended and the next chunk",
        "        gets a matching opening fence prepended.  This keeps markdown",
        "        code blocks rendered correctly across split messages.",
        '        """',
        "        if len(text) <= max_len:",
        "            return [text]",
        "",
        "        chunks: list[str] = []",
        "        current: list[str] = []",
        "        current_len = 0",
        f'        fence_open: str = ""  # e.g. "{fence}python"',
        "",
        "        def _flush() -> None:",
        "            nonlocal fence_open",
        '            body = "".join(current).rstrip("\\n")',
        "            if fence_open:",
        f'                body += "\\n{fence}"  # close dangling fence',
        "            chunks.append(body)",
        "            current.clear()",
        "",
        '        for line in text.split("\\n"):',
        '            line_with_nl = line + "\\n"',
        "            stripped = line.strip()",
        "",
        f'            if stripped.startswith(("{fence}", "{tilde_fence}")):'
        ,
        "                if fence_open:",
        '                    fence_open = ""',
        "                else:",
        "                    fence_open = stripped",
        "",
        "            # Flush if adding this line would exceed the limit.",
        "            if current and current_len + len(line_with_nl) > max_len:",
        "                saved_fence = fence_open",
        "                _flush()",
        "                current_len = 0",
        "                # Re-open the fence in the next chunk.",
        "                if saved_fence:",
        "                    fence_open = saved_fence",
        '                    reopener = saved_fence + "\\n"',
        "                    current.append(reopener)",
        "                    current_len += len(reopener)",
        "",
        "            # Single line exceeds max_len -> hard-split.",
        "            if len(line_with_nl) > max_len:",
        "                for i in range(0, len(line), max_len):",
        "                    chunks.append(line[i : i + max_len])",
        "            else:",
        "                current.append(line_with_nl)",
        "                current_len += len(line_with_nl)",
        "",
        "        if current:",
        '            chunks.append("".join(current).rstrip("\\n"))',
        "",
        '        return [c for c in chunks if c.strip()]',
        "",
    ]

    send_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("async def send("):
            send_idx = i
            break

    for j, cl in enumerate(chunk_text_lines):
        lines.insert(send_idx + j, cl)

    # ---- Patch 3: Modify send() — add docstring note + chunking ----
    for i, line in enumerate(lines):
        if "- If neither is provided, this raises ValueError." in line:
            lines.insert(
                i + 1,
                "        - Messages exceeding 2000 chars are automatically"
                " split into",
            )
            lines.insert(
                i + 2,
                "            multiple messages preserving markdown"
                " code fences.",
            )
            break

    for i, line in enumerate(lines):
        if "await target.send(text)" in line and "file=" not in line:
            lines[i] = (
                "        for chunk in"
                " self._chunk_text(text, self._DISCORD_MAX_LEN):"
            )
            lines.insert(i + 1, "            await target.send(chunk)")
            break

    # ---- Write clean output ----
    output = "\n".join(lines)
    target = "src/copaw/app/channels/discord_/channel.py"
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(output)

    new_line_count = len(lines)
    print(f"Written {len(output)} chars, {new_line_count} lines")

    # Verify no BOM
    with open(target, "rb") as f:
        first_bytes = f.read(10)
    if first_bytes.startswith(b"\xef\xbb\xbf"):
        print("WARNING: BOM detected!")
    else:
        print("OK: No BOM")

    # Verify no corrupted chars
    with open(target, "r", encoding="utf-8") as f:
        content = f.read()
    if "\u93ae" in content or "\u9472" in content:
        print("WARNING: Corrupted chars detected!")
    else:
        print("OK: No corrupted chars")

    print("Done!")


if __name__ == "__main__":
    main()
