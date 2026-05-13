const OPEN_EXTERNAL_PROTOCOLS = new Set(["http:", "https:", "file:"]);

export function isOpenableExternalLink(url: string): boolean {
  try {
    return OPEN_EXTERNAL_PROTOCOLS.has(new URL(url).protocol);
  } catch {
    return false;
  }
}

/**
 * Open an external URL, using the pywebview bridge in desktop app or
 * window.open in browser.
 *
 * @param url - The URL to open
 * @param target - Target window name (default: "_blank")
 * @param features - Window features string (default: "noopener,noreferrer")
 */
export function openExternalLink(
  url: string,
  target: string = "_blank",
  features: string = "noopener,noreferrer",
): void {
  if (!isOpenableExternalLink(url)) return;

  const pywebview = (window as any).pywebview;
  if (pywebview?.api?.open_external_link) {
    // Desktop app: use pywebview bridge to open in system browser
    pywebview.api.open_external_link(url);
  } else {
    // Web browser: use standard window.open
    window.open(url, target, features);
  }
}
