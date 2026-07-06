"use client";

import { useEffect } from "react";
import type { ChatRole } from "@/types/chat";
import { useTypewriter } from "@/shared/ui-kit/useTypewriter";

interface MessageBubbleProps {
  role: ChatRole;
  content: string;
  attachments?: string[];
  /** Reveal content with a typewriter effect (off by default). */
  animate?: boolean;
  /** Fires as revealed text grows — lets the parent keep scroll pinned. */
  onTypingTick?: () => void;
}

/** Presentational chat bubble. No store/service access. */
export function MessageBubble({
  role,
  content,
  attachments,
  animate = false,
  onTypingTick,
}: MessageBubbleProps) {
  const isUser = role === "user";
  const { visible, done } = useTypewriter(content, animate);

  useEffect(() => {
    if (animate && !done) onTypingTick?.();
  }, [visible, animate, done, onTypingTick]);
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={[
          "max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm leading-relaxed",
          isUser
            ? "rounded-br-sm bg-blue-600 text-white"
            : "rounded-bl-sm bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100",
        ].join(" ")}
      >
        {attachments && attachments.length > 0 && (
          <ul className="mb-1.5 flex flex-wrap gap-1.5" aria-label="Attachments">
            {attachments.map((name, i) => (
              <li
                key={`${name}-${i}`}
                className={[
                  "rounded-md px-1.5 py-0.5 text-xs",
                  isUser
                    ? "bg-blue-500/60 text-blue-50"
                    : "bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
                ].join(" ")}
              >
                📄 {name}
              </li>
            ))}
          </ul>
        )}
        {visible}
        {animate && !done && (
          <span
            aria-hidden="true"
            className="ml-0.5 inline-block h-[1em] w-[2px] animate-pulse bg-current align-text-bottom"
          />
        )}
      </div>
    </div>
  );
}
