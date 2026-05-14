import { Marked } from "marked";
import { describe, expect, it } from "vitest";
import {
  normalizeMarkdownPayloadLineBreaks,
  normalizeMarkdownTableLineBreaks,
} from "./markdown";

const markedLikeChatRenderer = new Marked({
  renderer: {
    html(token) {
      const text = token.text || token.raw || "";
      return text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    },
  },
});

describe("markdown helpers", () => {
  it("normalizes br tags inside markdown table rows", () => {
    const markdown = [
      "| Name | Notes |",
      "| --- | --- |",
      "| Alpha | first<br>second<br />third |",
    ].join("\n");

    expect(normalizeMarkdownTableLineBreaks(markdown)).toContain(
      "first&#10;second&#10;third",
    );
  });

  it("leaves non-table br tags unchanged", () => {
    expect(normalizeMarkdownTableLineBreaks("first<br>second")).toBe(
      "first<br>second",
    );
  });

  it("normalizes nested response payload text", () => {
    const payload = {
      object: "response",
      output: [
        {
          content: [
            {
              type: "text",
              text: "| A | B |\n| --- | --- |\n| x | y<br>z |",
            },
          ],
        },
      ],
    };

    expect(normalizeMarkdownPayloadLineBreaks(payload)).toEqual({
      object: "response",
      output: [
        {
          content: [
            {
              type: "text",
              text: "| A | B |\n| --- | --- |\n| x | y&#10;z |",
            },
          ],
        },
      ],
    });
  });

  it("keeps normalized table breaks renderable when raw html is escaped", () => {
    const content = normalizeMarkdownTableLineBreaks(
      "| A | B |\n| --- | --- |\n| x | y<br>z |",
    );
    const html = markedLikeChatRenderer.parse(content) as string;

    expect(html).toContain("<td>y&#10;z</td>");
    expect(html).not.toContain("&lt;br");

    const container = document.createElement("div");
    container.innerHTML = html;
    const cell = container.querySelector("tbody td:nth-child(2)");
    expect(cell?.textContent).toBe("y\nz");
  });
});
