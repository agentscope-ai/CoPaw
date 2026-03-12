import { getApiUrl, getApiToken } from "./config";

function extractErrorMessage(payload: unknown): string {
  if (!payload) return "";
  if (typeof payload === "string") return payload.trim();
  if (Array.isArray(payload)) {
    return payload.map(extractErrorMessage).filter(Boolean).join("; ");
  }
  if (typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    for (const key of ["detail", "message", "msg", "error"]) {
      const value = record[key];
      const message = extractErrorMessage(value);
      if (message) return message;
    }
    try {
      return JSON.stringify(payload);
    } catch {
      return "";
    }
  }
  return String(payload);
}

export class ApiError extends Error {
  status: number;
  statusText: string;
  detail: string;

  constructor(status: number, statusText: string, detail: string) {
    super(detail || `Request failed: ${status} ${statusText}`);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.detail = detail;
  }
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
  const url = getApiUrl(path);
  const method = options.method || "GET";
  const headers = buildHeaders(method, options.headers);

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    let detail = "";

    if (text) {
      try {
        detail = extractErrorMessage(JSON.parse(text));
      } catch {
        detail = text.trim();
      }
    }

    throw new ApiError(response.status, response.statusText, detail);
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
