import type {
  SendMessageRequest,
  SendMessageResponse,
} from "@/types/chat";

/**
 * Real chat endpoints on the backend gateway:
 *   POST {API_BASE_URL}/api/chat        — JSON, prompt only
 *   POST {API_BASE_URL}/api/chat/files  — multipart, prompt + image/PDF files
 *
 * The gateway wraps every payload in the shared REST envelope:
 *   { status: "Success" | "Failed", data?: T, error_text?: string }
 * This module is the only place that knows about that wire format.
 */
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/** Wire envelope returned by every gateway endpoint. */
interface ApiResponse<T> {
  status: "Success" | "Failed";
  data?: T | null;
  error_text?: string | null;
}

/** Payload of a successful /api/chat call.
 *
 * The gateway is a pure proxy: this is the agent's OrchestrationResult passed
 * through unchanged, so the answer field is `answer` (not `reply`) and the agent
 * supplies the `thread_id`. */
interface ChatReply {
  answer: string;
  /** Thread key the agent stored this turn under (snake_case on the wire). */
  thread_id?: string;
}

/** Error raised when the gateway is unreachable or returns a failure. */
export class ChatServiceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ChatServiceError";
  }
}

export async function sendChatMessage(
  request: SendMessageRequest,
  signal?: AbortSignal,
): Promise<SendMessageResponse> {
  const prompt = request.prompt.trim();
  if (!prompt) {
    throw new ChatServiceError("A text prompt is required.");
  }

  const fileCount = request.files?.length ?? 0;
  if (fileCount > 1) {
    throw new ChatServiceError("Only one file can be attached per message.");
  }
  const hasFiles = fileCount > 0;

  let response: Response;
  if (hasFiles) {
    const form = new FormData();
    form.append("prompt", prompt);
    if (request.threadId) form.append("thread_id", request.threadId);
    for (const file of request.files!) form.append("files", file, file.name);
    response = await fetch(`${API_BASE_URL}/api/chat/files`, {
      method: "POST",
      body: form,
      signal,
    });
  } else {
    response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        ...(request.threadId ? { thread_id: request.threadId } : {}),
      }),
      signal,
    });
  }

  if (!response.ok) {
    // Errors carry honest status codes but still ship the envelope body —
    // surface its error_text when present.
    let detail: string | null = null;
    try {
      const failed = (await response.json()) as ApiResponse<ChatReply>;
      detail = failed.error_text ?? null;
    } catch {
      // non-JSON error body — fall back to the status code
    }
    throw new ChatServiceError(
      detail ?? `Gateway request failed with HTTP ${response.status}`,
    );
  }

  const envelope = (await response.json()) as ApiResponse<ChatReply>;

  if (envelope.status !== "Success" || !envelope.data?.answer) {
    throw new ChatServiceError(
      envelope.error_text ?? "Gateway returned no reply",
    );
  }

  return {
    reply: envelope.data.answer,
    ...(envelope.data.thread_id ? { threadId: envelope.data.thread_id } : {}),
  };
}

/** Payload of a successful thread deletion. */
interface DeleteThreadReply {
  thread_id: string;
  deleted: boolean;
}

/**
 * Delete a conversation thread (messages + stored documents) on the backend.
 * Resolves on success; throws ChatServiceError on any failure.
 */
export async function deleteChatThread(
  threadId: string,
  signal?: AbortSignal,
): Promise<void> {
  const key = threadId.trim();
  if (!key) {
    throw new ChatServiceError("A thread id is required.");
  }

  const response = await fetch(
    `${API_BASE_URL}/api/chat/threads/${encodeURIComponent(key)}`,
    { method: "DELETE", signal },
  );

  let envelope: ApiResponse<DeleteThreadReply> | null = null;
  try {
    envelope = (await response.json()) as ApiResponse<DeleteThreadReply>;
  } catch {
    // non-JSON body — fall through to the status-based error below
  }

  if (!response.ok || !envelope || envelope.status !== "Success") {
    throw new ChatServiceError(
      envelope?.error_text ??
        `Gateway request failed with HTTP ${response.status}`,
    );
  }
}
