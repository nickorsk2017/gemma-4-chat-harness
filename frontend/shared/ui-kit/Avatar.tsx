import type { ChatRole } from "@/types/chat";
import { PersonIcon, StarIcon } from "@/shared/ui-kit/icons";

interface AvatarProps {
  role: ChatRole;
}

/** Circular speaker mark shown beside a message row. Decorative: the role is
 * already conveyed by the bubble's own alignment and text. */
export function Avatar({ role }: AvatarProps) {
  const isUser = role === "user";
  return (
    <span
      aria-hidden="true"
      className={[
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-full",
        isUser
          ? "bg-hairline text-muted"
          : "bg-accent-soft text-accent",
      ].join(" ")}
    >
      {isUser ? (
        <PersonIcon className="h-5 w-5" />
      ) : (
        <StarIcon className="h-5 w-5" />
      )}
    </span>
  );
}
