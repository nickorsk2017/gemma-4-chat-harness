import { CHAT_STORAGE_KEY, useChatStore } from "@/stores/chatStore";
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
    useChatStore.setState({ messages: [], threadId: null, hydrated: false });
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
    useChatStore.setState({ messages: [], threadId: null, hydrated: false });
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
