import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import type { ChatMessage, ChatRole, GuardrailInfo } from "@/types/chat";
import { deleteChatThread, sendChatMessage } from "@/services/chatService";

/** Shown in place of an answer when the turn ran out of time. */
export const TURN_TIMEOUT_MESSAGE = "Please repeat your request";

/** Failure codes the user can act on by re-sending the same turn. */
const RETRYABLE_CODES = new Set(["turn_timeout", "rate_limited"]);

/**
 * Is this one of the failures the user can act on?
 *
 * Duck-typed on the code rather than `instanceof ChatServiceError`: class identity does
 * not survive a mocked module or a second copy of the bundle, and the store only needs
 * the code. Never matched on message text — that is prose, not a contract.
 */
function isRetryableFailure(err: unknown): boolean {
  return (
    typeof err === "object" &&
    err !== null &&
    "code" in err &&
    RETRYABLE_CODES.has((err as { code?: unknown }).code as string)
  );
}

/** What has to be kept to be able to send the same turn again. */
interface PendingRequest {
  prompt: string;
  files?: File[];
}

/** localStorage key the durable chat slice is persisted under. */
export const CHAT_STORAGE_KEY = "agent-chat";

interface ChatState {
  messages: ChatMessage[];
  isSending: boolean;
  error: string | null;
  /**
   * Server-side conversation thread key. Adopted from the first reply and
   * sent with every subsequent message so the agent keeps history and
   * uploaded-document text across turns. Reset together with the chat.
   */
  threadId: string | null;
  /**
   * True once the persisted slice has been rehydrated from localStorage.
   * SSR-safe hydration: the store starts empty on both server and client,
   * and the chat feature triggers rehydration after mount.
   */
  hydrated: boolean;
  /**
   * Send a user prompt (with optional image/PDF attachments) to the agent.
   * The text prompt is mandatory — files are never sent without one.
   */
  send: (prompt: string, files?: File[], isRetry?: boolean) => Promise<void>;
  /**
   * The turn that ran out of time, kept so `retry` has something to re-send.
   * Not persisted: a File cannot survive localStorage, and a retry only makes
   * sense inside the session that saw the timeout.
   */
  pending: PendingRequest | null;
  /**
   * Re-send the turn that timed out, on the same thread and flagged as a retry
   * so the agent does not store it as a second question. Removes the placeholder
   * first, so a successful retry leaves no orphan behind.
   */
  retry: () => Promise<void>;
  reset: () => void;
  /**
   * Reset the conversation on the backend: delete the server-side thread by
   * `threadId`, then clear local state (including the persisted slice).
   * Returns true on success — the view reloads the page only then; on failure
   * the transcript is kept and `error` is set (no reload, R5).
   */
  clearThread: () => Promise<boolean>;
}

function makeMessage(
  role: ChatRole,
  content: string,
  attachments?: string[],
  guardrails?: GuardrailInfo,
): ChatMessage {
  return {
    id:
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    role,
    content,
    ...(attachments && attachments.length > 0 ? { attachments } : {}),
    ...(guardrails ? { guardrails } : {}),
    createdAt: Date.now(),
  };
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      isSending: false,
      error: null,
      threadId: null,
      hydrated: false,
      pending: null,

      send: async (prompt: string, files?: File[], isRetry = false) => {
        const text = prompt.trim();
        // A text prompt is mandatory: attachments alone are never sent.
        if (!text || get().isSending) return;

        const names = files?.map((f) => f.name);
        const userMessage = makeMessage("user", text, names);
        set((state) => ({
          messages: [...state.messages, userMessage],
          isSending: true,
          error: null,
        }));

        try {
          // The request lives in the service layer, never in the store itself.
          const { reply, threadId, guardrails } = await sendChatMessage({
            prompt: text,
            files,
            threadId: get().threadId ?? undefined,
            ...(isRetry ? { isRetry: true } : {}),
          });
          set((state) => ({
            messages: [
              ...state.messages,
              makeMessage("assistant", reply, undefined, guardrails),
            ],
            isSending: false,
            // Keep the established thread; adopt the gateway's key on first turn.
            threadId: state.threadId ?? threadId ?? null,
          }));
        } catch (err) {
          // A timed-out or rate-limited turn is one the user can act on, so it goes
          // into the transcript with an action rather than into the error line.
          // Branching on the code, never on the message text.
          if (isRetryableFailure(err)) {
            const placeholder = makeMessage("assistant", TURN_TIMEOUT_MESSAGE);
            set((state) => ({
              messages: [...state.messages, { ...placeholder, retryable: true }],
              isSending: false,
              error: null,
              pending: { prompt: text, ...(files ? { files } : {}) },
            }));
            return;
          }
          set({
            isSending: false,
            error:
              err instanceof Error && err.message
                ? err.message
                : "Failed to get a response from the agent. Please try again.",
          });
        }
      },

      retry: async () => {
        const pending = get().pending;
        if (!pending || get().isSending) return;
        // Drop the placeholder and the user message the failed turn added: `send`
        // re-adds the user message, and the agent never stored the failed turn.
        set((state) => ({
          messages: state.messages.filter((m) => !m.retryable).slice(0, -1),
          pending: null,
        }));
        await get().send(pending.prompt, pending.files, true);
      },

      reset: () =>
        set({
          messages: [],
          isSending: false,
          error: null,
          threadId: null,
          pending: null,
        }),

      clearThread: async () => {
        if (get().isSending) return false;
        const threadId = get().threadId;
        // Nothing stored server-side yet — just clear the local slice (R4).
        if (!threadId) {
          get().reset();
          return true;
        }
        set({ isSending: true, error: null });
        try {
          // The request lives in the service layer, never in the store itself.
          await deleteChatThread(threadId);
          get().reset();
          return true;
        } catch (err) {
          set({
            isSending: false,
            error:
              err instanceof Error && err.message
                ? err.message
                : "Failed to reset the chat. Please try again.",
          });
          return false;
        }
      },
    }),
    {
      name: CHAT_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      // Durable slice only — never persist transient request state.
      // The retry entry is session-scoped (R18): `pending` holds the prompt and the
      // File objects, and neither survives localStorage, so persisting the offer to
      // re-send would restore a button with nothing behind it. The failed turn's own
      // user message stays — the user did ask; they simply got no answer.
      partialize: (state) => ({
        messages: state.messages.filter((m) => !m.retryable),
        threadId: state.threadId,
      }),
      // SSR safety: server HTML and the client's first render both see the
      // empty store; ChatView calls `useChatStore.persist.rehydrate()` after
      // mount (see onRehydrateStorage -> `hydrated`).
      skipHydration: true,
      onRehydrateStorage: () => () => {
        useChatStore.setState({ hydrated: true });
      },
    },
  ),
);
