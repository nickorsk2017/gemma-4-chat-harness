import type { ChatRole } from "@/types/chat";
import { Avatar } from "@/shared/ui-kit/Avatar";
import { formatTime } from "@/shared/ui-kit/formatTime";

interface MessageRowProps {
  role: ChatRole;
  /** Epoch millis; omitted when the row is a transient status. */
  createdAt?: number;
  children: React.ReactNode;
}

/** Lays out one turn: avatar on the speaker's side, bubble, timestamp beneath.
 * The bubble body itself is supplied by the caller. */
export function MessageRow({ role, createdAt, children }: MessageRowProps) {
  const isUser = role === "user";
  return (
    <div
      className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      <Avatar role={role} />
      <div
        className={`flex min-w-0 max-w-[78%] flex-col ${isUser ? "items-end" : "items-start"}`}
      >
        {children}
        {createdAt !== undefined && (
          <time
            dateTime={new Date(createdAt).toISOString()}
            className="mt-1.5 px-1 text-xs text-muted"
          >
            {formatTime(createdAt)}
          </time>
        )}
      </div>
    </div>
  );
}
