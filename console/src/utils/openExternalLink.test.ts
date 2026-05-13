import { describe, expect, it, vi, afterEach } from "vitest";
import { isOpenableExternalLink, openExternalLink } from "./openExternalLink";

describe("openExternalLink", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    delete (window as any).pywebview;
  });

  it("allows http, https, and file URLs", () => {
    expect(isOpenableExternalLink("https://example.com")).toBe(true);
    expect(isOpenableExternalLink("http://example.com")).toBe(true);
    expect(isOpenableExternalLink("file:///Users/test/file.txt")).toBe(true);
  });

  it("rejects relative and script URLs", () => {
    expect(isOpenableExternalLink("/chat")).toBe(false);
    expect(isOpenableExternalLink("javascript:alert(1)")).toBe(false);
  });

  it("uses the pywebview bridge when available", () => {
    const open = vi.fn();
    (window as any).pywebview = {
      api: {
        open_external_link: open,
      },
    };

    openExternalLink("file:///Users/test/file.txt");

    expect(open).toHaveBeenCalledWith("file:///Users/test/file.txt");
  });
});
