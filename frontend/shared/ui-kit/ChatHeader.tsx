import { Badge } from "@/shared/ui-kit/Badge";
import { Avatar } from "@/shared/ui-kit/Avatar";

interface ChatHeaderProps {
  title: string;
  badge: string;
  subtitle: string;
  /** Right-aligned action slot. */
  action: React.ReactNode;
}

/** Title block of the chat card: agent mark, name, tag, subtitle and one action. */
export function ChatHeader({
  title,
  badge,
  subtitle,
  action,
}: ChatHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        <Avatar role="assistant" />
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight">{title}</h1>
            <Badge label={badge} />
          </div>
          <p className="text-xs text-muted">{subtitle}</p>
        </div>
      </div>
      {action}
    </div>
  );
}
