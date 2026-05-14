import { beforeEach, describe, expect, it, vi } from "vitest";

const { mockDeleteChat, mockGetChat, mockListChats } = vi.hoisted(() => ({
  mockDeleteChat: vi.fn(),
  mockGetChat: vi.fn(),
  mockListChats: vi.fn(),
}));

vi.mock("../../../api", () => ({
  default: {
    deleteChat: mockDeleteChat,
    getChat: mockGetChat,
    listChats: mockListChats,
  },
}));

import { SessionApi } from "./index";

const STORAGE_PREFIX = "qwenpaw_pending_user_msg_";

function chatHistory(messages: unknown[] = [], status = "idle") {
  return {
    id: "chat-1",
    session_id: "console:default",
    user_id: "default",
    channel: "console",
    status,
    messages,
  };
}

function chatSpec(id: string, sessionId = "console:default") {
  return {
    id,
    name: "Chat",
    session_id: sessionId,
    user_id: "default",
    channel: "console",
    meta: {},
    status: "idle",
  };
}

function userMessage(text: string, id = text) {
  return {
    id,
    role: "user",
    content: [{ type: "text", text }],
  };
}

interface RuntimeMessage {
  role?: string;
  cards?: Array<{
    data?: {
      input?: Array<{
        content?: Array<{ text?: string }>;
      }>;
    };
  }>;
}

function userTexts(session: { messages?: RuntimeMessage[] }): string[] {
  return (session.messages || [])
    .filter((message) => message.role === "user")
    .map((message) =>
      (message.cards?.[0]?.data?.input?.[0]?.content || [])
        .map((part: { text?: string }) => part.text || "")
        .join("\n"),
    );
}

describe("SessionApi pending user messages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    mockListChats.mockResolvedValue([]);
  });

  it("keeps interrupted user messages visible when backend history is empty", async () => {
    const sessionApi = new SessionApi();
    sessionApi.setLastUserMessage("chat-1", "original request");
    mockGetChat.mockResolvedValue(chatHistory());

    const session = await sessionApi.getSession("chat-1");

    expect(userTexts(session)).toEqual(["original request"]);
    expect(sessionStorage.getItem(`${STORAGE_PREFIX}chat-1`)).toContain(
      "original request",
    );
  });

  it("clears cached user messages once backend history contains them", async () => {
    const sessionApi = new SessionApi();
    sessionApi.setLastUserMessage("chat-1", "persisted request");
    mockGetChat.mockResolvedValue(
      chatHistory([userMessage("persisted request")]),
    );

    const session = await sessionApi.getSession("chat-1");

    expect(userTexts(session)).toEqual(["persisted request"]);
    expect(sessionStorage.getItem(`${STORAGE_PREFIX}chat-1`)).toBeNull();
  });

  it("preserves earlier interrupted messages when a retry reaches backend first", async () => {
    const sessionApi = new SessionApi();
    sessionApi.setLastUserMessage("chat-1", "original request");
    sessionApi.setLastUserMessage("chat-1", "retry request");
    mockGetChat.mockResolvedValue(chatHistory([userMessage("retry request")]));

    const session = await sessionApi.getSession("chat-1");

    expect(userTexts(session)).toEqual(["original request", "retry request"]);
    expect(sessionStorage.getItem(`${STORAGE_PREFIX}chat-1`)).toContain(
      "original request",
    );
  });

  it("moves cached messages from temporary ids to resolved backend ids", async () => {
    const sessionApi = new SessionApi();
    sessionApi.setLastUserMessage("123456789", "draft request");
    mockListChats.mockResolvedValue([chatSpec("real-chat-id", "123456789")]);
    mockGetChat.mockResolvedValue(chatHistory());

    await sessionApi.updateSession({ id: "123456789" });
    const session = await sessionApi.getSession("123456789");

    expect(sessionStorage.getItem(`${STORAGE_PREFIX}123456789`)).toBeNull();
    expect(sessionStorage.getItem(`${STORAGE_PREFIX}real-chat-id`)).toContain(
      "draft request",
    );
    expect(userTexts(session)).toEqual(["draft request"]);
  });
});
