declare const BASE_URL: string;
declare const TOKEN: string;

/**
 * Get the full API URL with /api prefix
 * @param path - API path (e.g., "/models", "/skills")
 * @returns Full API URL (e.g., "http://localhost:8088/api/models" or "/api/models")
 */
export function getApiUrl(path: string): string {
  const base = BASE_URL || "";
  const apiPrefix = "/api";
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  // In desktop app, always call backend on fixed localhost port.
  if (isTauri()) {
    return `http://127.0.0.1:8088${apiPrefix}${normalizedPath}`;
  }

  // When served over http(s), prefer same-origin backend.
  if (
    typeof window !== "undefined" &&
    /^https?:\/\//.test(window.location.origin)
  ) {
    return `${window.location.origin}${apiPrefix}${normalizedPath}`;
  }

  // If BASE_URL is set (e.g., "http://localhost:8088"), use it
  // Otherwise, use relative path (works when served by backend)
  if (base && base.startsWith("http")) {
    // Ensure we do not duplicate /api when BASE_URL already includes it.
    const baseTrimmed = base.endsWith("/") ? base.slice(0, -1) : base;
    const baseWithoutApi = baseTrimmed.endsWith(apiPrefix)
      ? baseTrimmed.slice(0, -apiPrefix.length)
      : baseTrimmed;
    return `${baseWithoutApi}${apiPrefix}${normalizedPath}`;
  }

  // Relative path - works when frontend is served by the backend
  return `${apiPrefix}${normalizedPath}`;
}

/**
 * Get the API token
 * @returns API token string or empty string
 */
export function getApiToken(): string {
  return typeof TOKEN !== "undefined" ? TOKEN : "";
}

/**
 * Check if running in Tauri desktop app
 */
export function isTauri(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const protocol = window.location?.protocol || "";
  const hostname = window.location?.hostname || "";
  if (protocol === "tauri:" || protocol === "asset:" || protocol === "file:") {
    return true;
  }
  if (
    hostname === "tauri.localhost" ||
    hostname.endsWith(".tauri.localhost")
  ) {
    return true;
  }

  return (
    "__TAURI_INTERNALS__" in window ||
    "__TAURI__" in window
  );
}

/**
 * Get the backend base URL for API calls
 * In Tauri app, defaults to http://127.0.0.1:8088
 * In browser, uses BASE_URL env or empty string (same-origin)
 */
export function getBackendBaseUrl(): string {
  // If explicitly set via env, use it
  if (BASE_URL) {
    return BASE_URL;
  }

  // In Tauri app, default to localhost backend
  if (isTauri()) {
    return "http://127.0.0.1:8088";
  }

  // In browser, use same-origin (empty string)
  return "";
}
