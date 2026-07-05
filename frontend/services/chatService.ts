import type {
  SendMessageRequest,
  SendMessageResponse,
} from "@/types/chat";

/**
 * Real chat endpoint: POST {API_BASE_URL}/api/chat on the backend gateway.
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

/** Payload of a successful /api/chat call. */
interface ChatReply {
  reply: string;
  subtasks?: number;
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
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: request.prompt }),
    signal,
  });

  if (!response.ok) {
    throw new ChatServiceError(
      `Gateway request failed with HTTP ${response.status}`,
    );
  }

  const envelope = (await response.json()) as ApiResponse<ChatReply>;

  if (envelope.status !== "Success" || !envelope.data?.reply) {
    throw new ChatServiceError(
      envelope.error_text ?? "Gateway returned no reply",
    );
  }

  return { reply: envelope.data.reply };
}
