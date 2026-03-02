import { getApiUrl, getApiToken } from "./config";

function buildHeaders(method?: string, extra?: HeadersInit): HeadersInit {
  const headers: HeadersInit = {};

  // Content-Type
  if (method && ["POST", "PUT", "PATCH"].includes(method.toUpperCase())) {
    headers["Content-Type"] = "application/json";
  }

  if (extra) {
    Object.assign(headers, extra);
  }

  const token = getApiToken();
  if (token) {
    (headers as Record<string, string>).Authorization = `Bearer ${token}`;
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
    throw new Error(
      `Request failed: ${response.status} ${response.statusText}${
        text ? ` - ${text}` : ""
      }`,
    );
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
