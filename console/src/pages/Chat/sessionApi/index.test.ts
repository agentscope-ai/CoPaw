import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const apiMocks = vi.hoisted(() => ({
  listChats: vi.fn(),
  deleteChat: vi.fn(),
}));

vi.mock("../../../api", () => ({
  default: apiMocks,
}));

vi.mock("../utils", () => ({
  toDisplayUrl: (url: string) => url,
}));

const buildChat = (id: string, sessionId: string) => ({
  id,
  name: "Test chat",
  session_id: sessionId,
  user_id: "default",
  channel: "console",
  meta: {},
  status: "idle",
  created_at: null,
  pinned: false,
});

const importSessionApi = async () => {
  vi.resetModules();
  const module = await import("./index");
  return module.default;
};

describe("sessionApi real id resolution", () => {
  beforeEach(() => {
    apiMocks.listChats.mockReset();
    apiMocks.deleteChat.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("retries a stale chat list before resolving a temporary session id", async () => {
    vi.useFakeTimers();
    const tempId = "1710000000000";
    apiMocks.listChats
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([buildChat("uuid-1", tempId)]);

    const sessionApi = await importSessionApi();
    const onResolved = vi.fn();
    sessionApi.onSessionIdResolved = onResolved;

    const resolved = sessionApi.getBackendIdForSession(tempId);
    await vi.advanceTimersByTimeAsync(250);

    await expect(resolved).resolves.toBe("uuid-1");
    expect(apiMocks.listChats).toHaveBeenCalledTimes(2);
    expect(onResolved).toHaveBeenCalledWith("uuid-1", tempId);
  });

  it("resolves a temporary session before deleting the backend chat", async () => {
    const tempId = "1710000000001";
    apiMocks.listChats.mockResolvedValueOnce([buildChat("uuid-2", tempId)]);
    apiMocks.deleteChat.mockResolvedValueOnce({ success: true });

    const sessionApi = await importSessionApi();

    await sessionApi.removeSession({ id: tempId });

    expect(apiMocks.deleteChat).toHaveBeenCalledWith("uuid-2");
  });
});
