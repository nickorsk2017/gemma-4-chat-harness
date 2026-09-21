"use client";

import { useEffect } from "react";
import type { ChatRole, GuardrailInfo } from "@/types/chat";
import { useTypewriter } from "@/shared/ui-kit/useTypewriter";
import { Markdown } from "@/shared/ui-kit/Markdown";

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
      className="mt-2 border-t border-hairline pt-1.5 text-xs text-muted"
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
    <div
      className={[
        "w-fit break-words px-4 py-2.5 text-sm leading-relaxed rounded-bubble",
        isUser
          ? "whitespace-pre-wrap bg-accent font-semibold text-accent-foreground"
          : "bg-bubble-agent text-bubble-agent-foreground",
      ].join(" ")}
    >
      {attachments && attachments.length > 0 && (
        <ul className="mb-1.5 flex flex-wrap gap-1.5" aria-label="Attachments">
          {attachments.map((name, i) => (
            <li
              key={`${name}-${i}`}
              className={[
                "rounded-md px-1.5 py-0.5 text-xs font-normal",
                isUser
                  ? "bg-white/20 text-accent-foreground"
                  : "bg-surface text-muted",
              ].join(" ")}
            >
              {name}
            </li>
          ))}
        </ul>
      )}
      {isUser ? visible : <Markdown source={visible} />}
      {!isUser && guardrails && <GuardrailNote info={guardrails} />}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          disabled={retryDisabled}
          className="mt-2 rounded-control border border-hairline px-2.5 py-1 text-xs font-medium text-foreground transition-colors hover:bg-surface disabled:opacity-50"
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
  );
}
