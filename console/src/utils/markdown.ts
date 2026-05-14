/**
 * Strip YAML frontmatter from the beginning of a markdown string.
 *
 * Many .md files start with a YAML header wrapped in `---` delimiters.
 * marked / XMarkdown renders `---` as <hr> and the YAML body as plain text.
 * This helper removes the frontmatter block before passing content to the renderer.
 */
export const stripFrontmatter = (s: string): string =>
  s.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/, "");

const HTML_LINE_BREAK_RE = /<br\s*\/?>/gi;
const HTML_LINE_BREAK_TEST_RE = /<br\s*\/?>/i;
const TABLE_SEPARATOR_RE = /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/;

const isTableLikeLine = (line: string): boolean => line.includes("|");

/**
 * Keep GFM table cells compatible with the chat Markdown renderer.
 *
 * The upstream Markdown component escapes raw HTML by default. In table cells,
 * users commonly emit `<br>` to force a line break, but that becomes literal
 * text. Replacing only table-row `<br>` tags with the HTML line-feed entity
 * preserves the existing safe HTML behavior while rendering as a visual break
 * because table cells use `white-space: pre`.
 */
export function normalizeMarkdownTableLineBreaks(markdown: string): string {
  if (
    !markdown ||
    !HTML_LINE_BREAK_TEST_RE.test(markdown) ||
    !markdown.includes("|")
  ) {
    return markdown;
  }

  const lines = markdown.split("\n");
  let insideTable = false;

  return lines
    .map((line, index) => {
      const isSeparator = TABLE_SEPARATOR_RE.test(line);
      const previousIsSeparator = TABLE_SEPARATOR_RE.test(
        lines[index - 1] || "",
      );
      const nextIsSeparator = TABLE_SEPARATOR_RE.test(lines[index + 1] || "");
      const isTableLine = isTableLikeLine(line);

      if (!isTableLine) {
        insideTable = false;
        return line;
      }

      const inTable =
        isSeparator || previousIsSeparator || nextIsSeparator || insideTable;
      insideTable = inTable;

      return inTable ? line.replace(HTML_LINE_BREAK_RE, "&#10;") : line;
    })
    .join("\n");
}

function normalizeMarkdownContent(value: unknown): unknown {
  if (typeof value === "string") {
    return normalizeMarkdownTableLineBreaks(value);
  }

  if (!Array.isArray(value)) {
    return value;
  }

  let changed = false;
  const normalized = value.map((item) => {
    if (!item || typeof item !== "object") {
      return item;
    }

    const record = item as Record<string, unknown>;
    if (record.type !== "text" || typeof record.text !== "string") {
      return item;
    }

    const text = normalizeMarkdownTableLineBreaks(record.text);
    if (text === record.text) {
      return item;
    }

    changed = true;
    return { ...record, text };
  });

  return changed ? normalized : value;
}

export function normalizeMarkdownPayloadLineBreaks<T>(payload: T): T {
  if (!payload || typeof payload !== "object") {
    return payload;
  }

  const record = payload as Record<string, unknown>;
  let next: Record<string, unknown> | null = null;
  const ensureNext = () => {
    if (!next) next = { ...record };
    return next;
  };

  if (record.type === "text" && typeof record.text === "string") {
    const text = normalizeMarkdownTableLineBreaks(record.text);
    if (text !== record.text) {
      ensureNext().text = text;
    }
  }

  if ("content" in record) {
    const content = normalizeMarkdownContent(record.content);
    if (content !== record.content) {
      ensureNext().content = content;
    }
  }

  if (Array.isArray(record.output)) {
    let changed = false;
    const output = record.output.map((item) => {
      const normalized = normalizeMarkdownPayloadLineBreaks(item);
      if (normalized !== item) changed = true;
      return normalized;
    });
    if (changed) {
      ensureNext().output = output;
    }
  }

  if (Array.isArray(record.input)) {
    let changed = false;
    const input = record.input.map((item) => {
      const normalized = normalizeMarkdownPayloadLineBreaks(item);
      if (normalized !== item) changed = true;
      return normalized;
    });
    if (changed) {
      ensureNext().input = input;
    }
  }

  return (next || record) as T;
}
