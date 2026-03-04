import { getApiUrl, getApiToken } from "./config";

function buildDesktopFallbackUrl(path: string, isGet: boolean): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const rawUrl = `http://127.0.0.1:8088/api${normalizedPath}`;
  if (!isGet) return rawUrl;
  const sep = rawUrl.includes("?") ? "&" : "?";
  return `${rawUrl}${sep}_ts=${Date.now()}`;
}

function shouldRetryDesktop(url: string): boolean {
  return !url.startsWith("http://127.0.0.1:8088/");
}

function buildHeaders(method?: string, extra?: HeadersInit): Headers {
  // Normalize extra to a Headers instance for consistent handling
  const headers = extra instanceof Headers ? extra : new Headers(extra);

  // Only add Content-Type for methods that typically have a body
  if (method && ["POST", "PUT", "PATCH"].includes(method.toUpperCase())) {
    // Don't override if caller explicitly set Content-Type
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
  }

  // Add authorization token if available
  const token = getApiToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return headers;
}

export async function request<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const method = options.method || "GET";
  const isGet = method.toUpperCase() === "GET";
  const rawUrl = getApiUrl(path);
  const url = isGet
    ? (() => {
        const sep = rawUrl.includes("?") ? "&" : "?";
        return `${rawUrl}${sep}_ts=${Date.now()}`;
      })()
    : rawUrl;
  const headers = buildHeaders(method, options.headers);

  const fetchOptions: RequestInit = {
    ...options,
    headers,
    cache: isGet ? "no-store" : options.cache,
  };
  let response: Response;
  try {
    response = await fetch(url, fetchOptions);
  } catch (err) {
    if (!shouldRetryDesktop(url)) {
      throw err;
    }
    response = await fetch(buildDesktopFallbackUrl(path, isGet), fetchOptions);
  }

  if (!response.ok) {
    if (shouldRetryDesktop(url) && response.status >= 400) {
      const fallbackRes = await fetch(
        buildDesktopFallbackUrl(path, isGet),
        fetchOptions,
      );
      if (fallbackRes.ok) {
        response = fallbackRes;
      } else {
        const text = await fallbackRes.text().catch(() => "");
        throw new Error(
          `Request failed: ${fallbackRes.status} ${fallbackRes.statusText}${
            text ? ` - ${text}` : ""
          }`,
        );
      }
    } else {
      const text = await response.text().catch(() => "");
      throw new Error(
        `Request failed: ${response.status} ${response.statusText}${
          text ? ` - ${text}` : ""
        }`,
      );
    }
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return (await response.text()) as unknown as T;
  }

  return (await response.json()) as T;
}
