"use client";

import { useEffect } from "react";
import type { ChatRole, GuardrailInfo } from "@/types/chat";
import { useTypewriter } from "@/shared/ui-kit/useTypewriter";

interface MessageBubbleProps {
  role: ChatRole;
  content: string;
  attachments?: string[];
  /** Reveal content with a typewriter effect (off by default). */
  animate?: boolean;
  /** Fires as revealed text grows — lets the parent keep scroll pinned. */
  onTypingTick?: () => void;
  /** Safety-gate outcome for this turn, when the gate did anything. */
  guardrails?: GuardrailInfo;
  /** Fires when the user asks to re-send a turn that ran out of time. */
  onRetry?: () => void;
  /** Disables the retry action while a request is in flight. */
  retryDisabled?: boolean;
}

/** Footnote under an assistant bubble explaining what the safety gate did.
 *
 * The redaction notice is shown in english verbatim: it is the exact wording the
 * model was given, and the user should see the same sentence rather than a
 * paraphrase of it. */
function GuardrailNote({ info }: { info: GuardrailInfo }) {
  const lines: string[] = [];
  if (info.notice) lines.push(info.notice);
  if (lines.length === 0) return null;

  return (
    <div
      className="mt-2 border-t border-gray-300 pt-1.5 text-xs text-gray-500 dark:border-gray-600 dark:text-gray-400"
      role="note"
    >
      {lines.map((line, i) => (
        <p key={i}>{line}</p>
      ))}
    </div>
  );
}

/** Presentational chat bubble. No store/service access. */
export function MessageBubble({
  role,
  content,
  attachments,
  animate = false,
  onTypingTick,
  guardrails,
  onRetry,
  retryDisabled = false,
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
        {!isUser && guardrails && <GuardrailNote info={guardrails} />}
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            disabled={retryDisabled}
            className="mt-2 rounded-md border border-gray-300 px-2.5 py-1 text-xs font-medium text-gray-700 hover:bg-gray-200 disabled:opacity-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
          >
            Retry
          </button>
        )}
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
