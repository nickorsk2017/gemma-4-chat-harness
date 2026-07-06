// Chat domain types. Ambient module: consumed via `@/types/chat`.

export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  /** Names of files attached to this (user) message. */
  attachments?: string[];
  /** epoch millis */
  createdAt: number;
}

/** Payload sent to the gateway. Files are optional; the prompt never is. */
export interface SendMessageRequest {
  prompt: string;
  files?: File[];
  /** Conversation thread key; omitted on the very first message. */
  threadId?: string;
}

/** Agent response. */
export interface SendMessageResponse {
  reply: string;
  /** Thread key the gateway checkpointed this turn under. */
  threadId?: string;
}
