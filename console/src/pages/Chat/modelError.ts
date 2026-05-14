export function extractErrorText(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;

  const record = payload as Record<string, unknown>;
  const candidates = [
    record.detail,
    record.message,
    record.error,
    record.error_message,
  ];

  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate.trim();
    }
    if (candidate && typeof candidate === "object") {
      const nested = extractErrorText(candidate);
      if (nested) return nested;
    }
  }

  return null;
}

export function payloadHasErrorSignal(
  payload: Record<string, unknown>,
): boolean {
  return (
    "detail" in payload ||
    "error" in payload ||
    "error_message" in payload ||
    payload.status === "failed" ||
    payload.status === "error"
  );
}

export async function readErrorResponse(
  response: Response,
): Promise<string | null> {
  try {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return extractErrorText(await response.clone().json());
    }
    const text = await response.clone().text();
    return text.trim() || null;
  } catch {
    return null;
  }
}
