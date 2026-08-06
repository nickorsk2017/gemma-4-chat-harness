// Chat domain types. Ambient module: consumed via `@/types/chat`.

export type ChatRole = "user" | "assistant";

/**
 * What the safety gate did to a turn. Produced by the guardrails service, carried
 * outward on the orchestrator result and forwarded unchanged by the gateway.
 */
export interface GuardrailInfo {
  /** PII types removed from the prompt before it reached the model. */
  redactedTypes: string[];
  /** The exact English notice shown to the user when data was redacted. */
  notice?: string;
  /** Policy refused the turn. */
  blocked: boolean;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  /**
   * Set on the assistant-side entry that replaces a turn which ran out of time.
   * The UI renders it with a retry action instead of as an answer.
   */
  retryable?: boolean;
  /** Names of files attached to this (user) message. */
  attachments?: string[];
  /** epoch millis */
  createdAt: number;
  /** Safety-gate outcome, present on assistant messages when anything happened. */
  guardrails?: GuardrailInfo;
}

/** Payload sent to the gateway. Files are optional; the prompt never is. */
export interface SendMessageRequest {
  prompt: string;
  files?: File[];
  /** Conversation thread key; omitted on the very first message. */
  threadId?: string;
  /**
   * True when re-sending a turn that ran out of time. The agent marks the stored
   * message so the retry is not read as the user asking a second question.
   */
  isRetry?: boolean;
}

/**
 * Machine-readable failure kinds from the gateway. Both are actionable: the one
 * failure the user can do something about, by re-sending.
 */
export type ChatErrorCode = "turn_timeout" | "rate_limited";

/** Agent response. */
export interface SendMessageResponse {
  reply: string;
  /** Thread key the gateway checkpointed this turn under. */
  threadId?: string;
  /** Safety-gate outcome for this turn, when the gate reported anything. */
  guardrails?: GuardrailInfo;
}
