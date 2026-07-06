"use client";

import { useCallback, useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { HeaderButton } from "@/shared/ui-kit/HeaderButton";
import { MessageBubble } from "@/shared/ui-kit/MessageBubble";
import { MessageInput } from "@/shared/ui-kit/MessageInput";

/**
 * Chat feature: wires the Zustand store to presentational ui-kit parts.
 * All page logic lives here; the route file only renders this component.
 */
export function ChatView() {
  const messages = useChatStore((s) => s.messages);
  const isSending = useChatStore((s) => s.isSending);
  const error = useChatStore((s) => s.error);
  const send = useChatStore((s) => s.send);
  const clearThread = useChatStore((s) => s.clearThread);
  const hydrated = useChatStore((s) => s.hydrated);

  const bottomRef = useRef<HTMLDivElement>(null);

  // Restore the persisted thread (threadId + messages) after mount only —
  // `skipHydration` keeps server HTML and the first client render identical.
  useEffect(() => {
    void useChatStore.persist.rehydrate();
  }, []);

  // Messages restored from storage must not (re-)animate: snapshot the ids
  // present once hydration completes; only later replies get the typewriter.
  const preexistingIds = useRef<Set<string> | null>(null);
  if (preexistingIds.current === null && hydrated) {
    preexistingIds.current = new Set(messages.map((m) => m.id));
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  // Keep the view pinned to the bottom while a reply is typing out.
  const handleTypingTick = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: "auto" });
  }, []);

  // Delete the server-side thread; reload the page ONLY on success so a
  // failure keeps the transcript and shows the store error instead.
  const handleReset = useCallback(async () => {
    const ok = await clearThread();
    if (ok) window.location.reload();
  }, [clearThread]);

  const lastMessage = messages[messages.length - 1];
  const isEmpty = messages.length === 0;

  return (
    <div className="mx-auto flex h-screen w-full max-w-2xl flex-col">
      <header className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-800">
        <div>
          <h1 className="text-base font-semibold">AI agent</h1>
          <p className="text-xs text-gray-500">
            Chat with the agent · attach images or PDFs for analysis
          </p>
        </div>
        <HeaderButton
          label="Reset chat"
          ariaLabel="Reset chat and delete its history"
          onClick={handleReset}
          disabled={isSending || !hydrated}
        />
      </header>

      <main className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {isEmpty && (
          <div className="flex h-full items-center justify-center text-center text-sm text-gray-400">
            Start a conversation — message the agent below.
          </div>
        )}

        {messages.map((m) => {
          const animate =
            m.role === "assistant" &&
            m.id === lastMessage?.id &&
            !preexistingIds.current?.has(m.id);
          return (
            <MessageBubble
              key={m.id}
              role={m.role}
              content={m.content}
              attachments={m.attachments}
              animate={animate}
              onTypingTick={animate ? handleTypingTick : undefined}
            />
          );
        })}

        {isSending && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-sm bg-gray-100 px-4 py-2 text-sm text-gray-500 dark:bg-gray-800">
              Agent is typing…
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-950/40">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      <footer className="border-t border-gray-200 px-4 py-3 dark:border-gray-800">
        <MessageInput onSend={send} disabled={isSending} />
      </footer>
    </div>
  );
}
