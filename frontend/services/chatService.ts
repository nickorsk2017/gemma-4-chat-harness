import type {
  ChatErrorCode,
  GuardrailInfo,
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
  /** Machine-readable failure kind; clients branch on this, never on error_text. */
  error_code?: string | null;
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
  /** Safety-gate outcome, snake_case on the wire (guardrails service contract). */
  guardrails?: {
    redacted_types?: string[];
    notice?: string | null;
    blocked?: boolean;
  };
}

/** Map the wire shape to the domain type. Returns undefined when nothing happened,
 * so an untouched turn carries no guardrail object at all. */
function toGuardrailInfo(raw: ChatReply["guardrails"]): GuardrailInfo | undefined {
  if (!raw) return undefined;
  const redactedTypes = raw.redacted_types ?? [];

  const blocked = raw.blocked ?? false;
  if (redactedTypes.length === 0 && !blocked) return undefined;
  return {
    redactedTypes,
    blocked,
    ...(raw.notice ? { notice: raw.notice } : {}),
  };
}

/** Error raised when the gateway is unreachable or returns a failure. */
export class ChatServiceError extends Error {
  /** Present when the gateway named the failure; `turn_timeout` is retryable. */
  readonly code?: ChatErrorCode;

  constructor(message: string, code?: ChatErrorCode) {
    super(message);
    this.name = "ChatServiceError";
    this.code = code;
  }
}

/** Narrow the wire string to the codes the UI knows how to act on. */
function toErrorCode(raw: string | null | undefined): ChatErrorCode | undefined {
  return raw === "turn_timeout" ? "turn_timeout" : undefined;
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
    if (request.isRetry) form.append("is_retry", "true");
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
        ...(request.isRetry ? { is_retry: true } : {}),
      }),
      signal,
    });
  }

  if (!response.ok) {
    // Errors carry honest status codes but still ship the envelope body —
    // surface its error_text when present.
    let detail: string | null = null;
    let code: ChatErrorCode | undefined;
    try {
      const failed = (await response.json()) as ApiResponse<ChatReply>;
      detail = failed.error_text ?? null;
      code = toErrorCode(failed.error_code);
    } catch {
      // non-JSON error body — fall back to the status code
    }
    throw new ChatServiceError(
      detail ?? `Gateway request failed with HTTP ${response.status}`,
      code,
    );
  }

  const envelope = (await response.json()) as ApiResponse<ChatReply>;

  if (envelope.status !== "Success" || !envelope.data?.answer) {
    throw new ChatServiceError(
      envelope.error_text ?? "Gateway returned no reply",
      toErrorCode(envelope.error_code),
    );
  }

  const guardrails = toGuardrailInfo(envelope.data.guardrails);
  return {
    reply: envelope.data.answer,
    ...(envelope.data.thread_id ? { threadId: envelope.data.thread_id } : {}),
    ...(guardrails ? { guardrails } : {}),
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
