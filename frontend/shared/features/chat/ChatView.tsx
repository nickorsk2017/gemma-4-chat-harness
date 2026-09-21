"use client";

import { useCallback, useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { ChatHeader } from "@/shared/ui-kit/ChatHeader";
import { ChatShell } from "@/shared/ui-kit/ChatShell";
import { HeaderButton } from "@/shared/ui-kit/HeaderButton";
import { MessageBubble } from "@/shared/ui-kit/MessageBubble";
import { MessageInput } from "@/shared/ui-kit/MessageInput";
import { MessageRow } from "@/shared/ui-kit/MessageRow";
import { RefreshIcon } from "@/shared/ui-kit/icons";

/**
 * Chat feature: wires the Zustand store to presentational ui-kit parts.
 * All page logic lives here; the route file only renders this component.
 */
export function ChatView() {
  const messages = useChatStore((s) => s.messages);
  const isSending = useChatStore((s) => s.isSending);
  const error = useChatStore((s) => s.error);
  const retry = useChatStore((s) => s.retry);
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
    <ChatShell
      header={
        <ChatHeader
          title="Gemma 4"
          badge="Chat"
          subtitle="Chat with the agent · attach images or PDFs for analysis"
          action={
            <HeaderButton
              label="Reset chat"
              ariaLabel="Reset chat and delete its history"
              icon={<RefreshIcon className="h-4 w-4" />}
              onClick={handleReset}
              disabled={isSending || !hydrated}
            />
          }
        />
      }
      footer={<MessageInput onSend={send} disabled={isSending} />}
    >
      {isEmpty && (
        <p className="flex h-full items-center justify-center text-center text-sm text-muted">
          Start a conversation — message the agent below.
        </p>
      )}

      {messages.map((m) => {
        const animate =
          m.role === "assistant" &&
          m.id === lastMessage?.id &&
          !preexistingIds.current?.has(m.id);
        return (
          <MessageRow key={m.id} role={m.role} createdAt={m.createdAt}>
            <MessageBubble
              role={m.role}
              content={m.content}
              attachments={m.attachments}
              guardrails={m.guardrails}
              animate={animate}
              onTypingTick={animate ? handleTypingTick : undefined}
              onRetry={m.retryable ? retry : undefined}
              retryDisabled={isSending}
            />
          </MessageRow>
        );
      })}

      {isSending && (
        <MessageRow role="assistant">
          <p className="rounded-bubble bg-bubble-agent px-4 py-2.5 text-sm text-muted">
            Agent is typing…
          </p>
        </MessageRow>
      )}

      {error && (
        <p className="rounded-control bg-danger-soft px-3 py-2 text-sm text-danger">
          {error}
        </p>
      )}

      <div ref={bottomRef} />
    </ChatShell>
  );
}
