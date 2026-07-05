import { sendChatMessage, ChatServiceError } from "@/services/chatService";

function jsonResponse(body: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    json: async () => body,
  } as Response;
}

describe("chatService (gateway REST)", () => {
  const fetchMock = jest.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    global.fetch = fetchMock as unknown as typeof fetch;
  });

  it("POSTs the prompt to /api/chat and returns the reply on Success", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ status: "Success", data: { reply: "Hello!", subtasks: 2 } }),
    );

    const res = await sendChatMessage({ prompt: "hi there" });

    expect(res).toEqual({ reply: "Hello!" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/api\/chat$/);
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(init.body)).toEqual({ prompt: "hi there" });
  });

  it("throws with error_text on a Failed envelope", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ status: "Failed", error_text: "orchestrator down" }),
    );

    await expect(sendChatMessage({ prompt: "hi" })).rejects.toThrow(
      "orchestrator down",
    );
  });

  it("throws when the envelope has no reply payload", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ status: "Success", data: null }));

    await expect(sendChatMessage({ prompt: "hi" })).rejects.toThrow(
      ChatServiceError,
    );
  });

  it("throws on a non-OK HTTP status", async () => {
    fetchMock.mockResolvedValue(jsonResponse({}, false, 500));

    await expect(sendChatMessage({ prompt: "hi" })).rejects.toThrow("HTTP 500");
  });

  it("passes the abort signal to fetch and rejects when aborted", async () => {
    const controller = new AbortController();
    controller.abort();
    fetchMock.mockImplementation((_url, init) => {
      if ((init as RequestInit).signal?.aborted) {
        return Promise.reject(new DOMException("Aborted", "AbortError"));
      }
      return Promise.resolve(jsonResponse({ status: "Success", data: { reply: "x" } }));
    });

    await expect(
      sendChatMessage({ prompt: "hi" }, controller.signal),
    ).rejects.toThrow();
    expect(fetchMock.mock.calls[0][1].signal).toBe(controller.signal);
  });
});
