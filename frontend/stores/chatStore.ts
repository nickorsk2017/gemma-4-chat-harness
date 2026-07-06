import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import type { ChatMessage, ChatRole } from "@/types/chat";
import { deleteChatThread, sendChatMessage } from "@/services/chatService";

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
  send: (prompt: string, files?: File[]) => Promise<void>;
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
): ChatMessage {
  return {
    id:
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    role,
    content,
    ...(attachments && attachments.length > 0 ? { attachments } : {}),
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

      send: async (prompt: string, files?: File[]) => {
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
          const { reply, threadId } = await sendChatMessage({
            prompt: text,
            files,
            threadId: get().threadId ?? undefined,
          });
          set((state) => ({
            messages: [...state.messages, makeMessage("assistant", reply)],
            isSending: false,
            // Keep the established thread; adopt the gateway's key on first turn.
            threadId: state.threadId ?? threadId ?? null,
          }));
        } catch (err) {
          set({
            isSending: false,
            error:
              err instanceof Error && err.message
                ? err.message
                : "Failed to get a response from the agent. Please try again.",
          });
        }
      },

      reset: () =>
        set({ messages: [], isSending: false, error: null, threadId: null }),

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
      partialize: (state) => ({
        messages: state.messages,
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
