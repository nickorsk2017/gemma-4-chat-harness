import {
  CHAT_STORAGE_KEY,
  TURN_TIMEOUT_MESSAGE,
  useChatStore,
} from "@/stores/chatStore";
import { deleteChatThread, sendChatMessage } from "@/services/chatService";

jest.mock("@/services/chatService", () => ({
  sendChatMessage: jest.fn(),
  deleteChatThread: jest.fn(),
}));

const sendChatMessageMock = sendChatMessage as jest.MockedFunction<
  typeof sendChatMessage
>;
const deleteChatThreadMock = deleteChatThread as jest.MockedFunction<
  typeof deleteChatThread
>;

describe("chatStore.send", () => {
  beforeEach(() => {
    localStorage.clear();
    useChatStore.getState().reset();
    sendChatMessageMock.mockReset();
    sendChatMessageMock.mockResolvedValue({ reply: "Merged answer" });
  });

  it("appends the user message then the assistant reply", async () => {
    await useChatStore.getState().send("Hello, agent");

    const { messages, isSending, error } = useChatStore.getState();
    expect(messages).toHaveLength(2);
    expect(messages[0].role).toBe("user");
    expect(messages[0].content).toBe("Hello, agent");
    expect(messages[1].role).toBe("assistant");
    expect(messages[1].content).toBe("Merged answer");
    expect(isSending).toBe(false);
    expect(error).toBeNull();
  });

  it("forwards attached files and records attachment names", async () => {
    const file = new File(["%PDF-1.4"], "report.pdf", {
      type: "application/pdf",
    });

    await useChatStore.getState().send("Summarize this", [file]);

    expect(sendChatMessageMock).toHaveBeenCalledWith({
      prompt: "Summarize this",
      files: [file],
    });
    const user = useChatStore.getState().messages[0];
    expect(user.attachments).toEqual(["report.pdf"]);
  });

  it("ignores empty prompts", async () => {
    await useChatStore.getState().send("   ");
    expect(useChatStore.getState().messages).toHaveLength(0);
    expect(sendChatMessageMock).not.toHaveBeenCalled();
  });

  it("never sends files without a text prompt", async () => {
    const file = new File(["x"], "photo.png", { type: "image/png" });

    await useChatStore.getState().send("", [file]);

    expect(useChatStore.getState().messages).toHaveLength(0);
    expect(sendChatMessageMock).not.toHaveBeenCalled();
  });

  it("surfaces the service error message when the service rejects", async () => {
    sendChatMessageMock.mockRejectedValue(new Error("prompt is required"));

    await useChatStore.getState().send("Hello");

    const { messages, isSending, error } = useChatStore.getState();
    expect(messages).toHaveLength(1); // user message only
    expect(isSending).toBe(false);
    expect(error).toBe("prompt is required");
  });
});

/**
 * Wipe in-memory state while keeping what localStorage held before the wipe.
 * `setState` goes through the persist middleware and overwrites storage, so the
 * stored slice is captured first and restored afterwards, as a real reload would.
 */
function simulateReload() {
  const stored = localStorage.getItem(CHAT_STORAGE_KEY);
  useChatStore.setState({ messages: [], threadId: null, hydrated: false });
  if (stored !== null) localStorage.setItem(CHAT_STORAGE_KEY, stored);
}

describe("chatStore persistence (localStorage)", () => {
  beforeEach(() => {
    localStorage.clear();
    useChatStore.getState().reset();
    sendChatMessageMock.mockReset();
    sendChatMessageMock.mockResolvedValue({ reply: "Hi", threadId: "t-1" });
  });

  it("persists messages and threadId, but never transient state", async () => {
    await useChatStore.getState().send("Hello");

    const raw = localStorage.getItem(CHAT_STORAGE_KEY);
    expect(raw).not.toBeNull();
    const persisted = JSON.parse(raw!).state;
    expect(persisted.threadId).toBe("t-1");
    expect(persisted.messages).toHaveLength(2);
    expect(persisted.isSending).toBeUndefined();
    expect(persisted.error).toBeUndefined();
  });

  it("restores messages and threadId on rehydrate (page reload)", async () => {
    await useChatStore.getState().send("Hello");

    // Simulate a reload: wipe in-memory state, keep localStorage.
    simulateReload();
    await useChatStore.persist.rehydrate();

    const state = useChatStore.getState();
    expect(state.hydrated).toBe(true);
    expect(state.threadId).toBe("t-1");
    expect(state.messages).toHaveLength(2);
    expect(state.messages[0].content).toBe("Hello");
    expect(state.messages[1].content).toBe("Hi");
  });

  it("continues the same thread after rehydrate", async () => {
    await useChatStore.getState().send("Hello");
    simulateReload();
    await useChatStore.persist.rehydrate();

    await useChatStore.getState().send("And again");

    expect(sendChatMessageMock).toHaveBeenLastCalledWith(
      expect.objectContaining({ prompt: "And again", threadId: "t-1" }),
    );
  });

  it("reset clears the persisted slice too", async () => {
    await useChatStore.getState().send("Hello");

    useChatStore.getState().reset();
    await useChatStore.persist.rehydrate();

    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(0);
    expect(state.threadId).toBeNull();
  });
});

describe("chatStore.clearThread", () => {
  beforeEach(() => {
    localStorage.clear();
    useChatStore.getState().reset();
    sendChatMessageMock.mockReset();
    deleteChatThreadMock.mockReset();
    sendChatMessageMock.mockResolvedValue({ reply: "Hi", threadId: "t-1" });
  });

  it("deletes the backend thread and clears local + persisted state", async () => {
    deleteChatThreadMock.mockResolvedValue(undefined);
    await useChatStore.getState().send("Hello");

    const ok = await useChatStore.getState().clearThread();

    expect(ok).toBe(true);
    expect(deleteChatThreadMock).toHaveBeenCalledWith("t-1");
    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(0);
    expect(state.threadId).toBeNull();
    const persisted = JSON.parse(localStorage.getItem(CHAT_STORAGE_KEY)!).state;
    expect(persisted.messages).toHaveLength(0);
    expect(persisted.threadId).toBeNull();
  });

  it("skips the backend when no thread exists yet", async () => {
    const ok = await useChatStore.getState().clearThread();

    expect(ok).toBe(true);
    expect(deleteChatThreadMock).not.toHaveBeenCalled();
  });

  it("keeps the transcript and surfaces the error when deletion fails", async () => {
    deleteChatThreadMock.mockRejectedValue(new Error("thread deletion failed"));
    await useChatStore.getState().send("Hello");

    const ok = await useChatStore.getState().clearThread();

    expect(ok).toBe(false);
    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(2); // transcript preserved
    expect(state.threadId).toBe("t-1");
    expect(state.error).toBe("thread deletion failed");
    expect(state.isSending).toBe(false);
  });
});

describe("chatStore — a turn that ran out of time", () => {
  beforeEach(() => {
    localStorage.clear();
    useChatStore.getState().reset();
    sendChatMessageMock.mockReset();
  });

  /** What the service throws when the gateway names the failure. */
  function timeoutError() {
    return Object.assign(new Error("the turn ran out of time"), {
      code: "turn_timeout",
    });
  }

  /** What the service throws when the gateway (or the orchestrator, via the
   * gateway) rejects the turn for being over the rate limit. */
  function rateLimitedError() {
    return Object.assign(new Error("rate limit exceeded"), {
      code: "rate_limited",
    });
  }

  it("offers a retry in the transcript instead of an error line", async () => {
    sendChatMessageMock.mockRejectedValue(timeoutError());

    await useChatStore.getState().send("Describe this image");

    const { messages, error, isSending } = useChatStore.getState();
    expect(messages).toHaveLength(2);
    expect(messages[1].role).toBe("assistant");
    expect(messages[1].content).toBe(TURN_TIMEOUT_MESSAGE);
    expect(messages[1].retryable).toBe(true);
    // The point of the branch: this failure is actionable, so it does not land in the
    // error line the way every other failure does.
    expect(error).toBeNull();
    expect(isSending).toBe(false);
  });

  it("A4: a rate-limited reply gets the same retryable/pending state as a timeout", async () => {
    sendChatMessageMock.mockRejectedValue(rateLimitedError());

    await useChatStore.getState().send("Describe this image");

    const { messages, error, isSending, pending } = useChatStore.getState();
    expect(messages).toHaveLength(2);
    expect(messages[1].role).toBe("assistant");
    expect(messages[1].content).toBe(TURN_TIMEOUT_MESSAGE);
    expect(messages[1].retryable).toBe(true);
    expect(error).toBeNull();
    expect(isSending).toBe(false);
    expect(pending).toEqual({ prompt: "Describe this image" });
  });

  it("any other failure still goes to the error line", async () => {
    sendChatMessageMock.mockRejectedValue(new Error("agent failed"));

    await useChatStore.getState().send("Hello");

    const state = useChatStore.getState();
    expect(state.error).toBe("agent failed");
    expect(state.messages.some((m) => m.retryable)).toBe(false);
  });

  it("re-sends the same prompt flagged as a retry, leaving no placeholder", async () => {
    sendChatMessageMock.mockRejectedValueOnce(timeoutError());
    await useChatStore.getState().send("Describe this image");

    sendChatMessageMock.mockResolvedValueOnce({ reply: "A red bicycle" });
    await useChatStore.getState().retry();

    expect(sendChatMessageMock).toHaveBeenLastCalledWith(
      expect.objectContaining({ prompt: "Describe this image", isRetry: true }),
    );
    const { messages, pending } = useChatStore.getState();
    // user + answer: the placeholder is gone and the question was not duplicated.
    expect(messages).toHaveLength(2);
    expect(messages[0].content).toBe("Describe this image");
    expect(messages[1].content).toBe("A red bicycle");
    expect(messages.some((m) => m.retryable)).toBe(false);
    expect(pending).toBeNull();
  });

  it("does not persist the retry offer — it dies with the session", async () => {
    sendChatMessageMock.mockRejectedValue(timeoutError());

    await useChatStore.getState().send("Describe this image");

    // `pending` holds the File objects and cannot be persisted, so a restored button
    // would have nothing to send. The offer must not outlive the session (R18/A14).
    const persisted = JSON.parse(localStorage.getItem(CHAT_STORAGE_KEY)!).state;
    expect(persisted.messages.some((m: { retryable?: boolean }) => m.retryable)).toBe(
      false,
    );
    expect(persisted.pending).toBeUndefined();
  });
});
