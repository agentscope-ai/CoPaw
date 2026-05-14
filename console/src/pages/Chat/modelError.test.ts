import { describe, expect, it } from "vitest";
import {
  extractErrorText,
  payloadHasErrorSignal,
  readErrorResponse,
} from "./modelError";

describe("model error helpers", () => {
  it("extracts error text from nested response payloads", () => {
    expect(
      extractErrorText({
        detail: {
          error: {
            message: "Invalid API key",
          },
        },
      }),
    ).toBe("Invalid API key");
  });

  it("does not treat normal message payloads as stream errors", () => {
    expect(
      payloadHasErrorSignal({ object: "message", message: "normal output" }),
    ).toBe(false);
    expect(payloadHasErrorSignal({ status: "error" })).toBe(true);
  });

  it("reads json and text error responses", async () => {
    await expect(
      readErrorResponse(
        new Response(JSON.stringify({ error: "Provider rejected request" }), {
          status: 502,
          headers: { "content-type": "application/json" },
        }),
      ),
    ).resolves.toBe("Provider rejected request");

    await expect(
      readErrorResponse(new Response("upstream unavailable", { status: 503 })),
    ).resolves.toBe("upstream unavailable");
  });
});
