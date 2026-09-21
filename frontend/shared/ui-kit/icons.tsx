/** Inline SVG glyph set for the chat UI. No icon package, `currentColor` only.
 *
 * Every glyph is decorative: the accessible name lives on the control that
 * wraps it, so each one is hidden from assistive technology. */

interface IconProps {
  className?: string;
}

function Svg({
  className,
  children,
}: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className ?? "h-4 w-4"}
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

/** Four-point star — the agent's mark. */
export function StarIcon({ className }: IconProps) {
  return (
    <Svg className={className}>
      <path
        d="M12 2.5c.4 3.9 2.6 6.1 6.5 6.5v2c-3.9.4-6.1 2.6-6.5 6.5h-2c-.4-3.9-2.6-6.1-6.5-6.5V9C7.4 8.6 9.6 6.4 10 2.5h2Z"
        fill="currentColor"
      />
    </Svg>
  );
}

/** Person silhouette — the user's mark. */
export function PersonIcon({ className }: IconProps) {
  return (
    <Svg className={className}>
      <circle cx="12" cy="8.5" r="3.6" fill="currentColor" />
      <path
        d="M4.8 20a7.2 7.2 0 0 1 14.4 0Z"
        fill="currentColor"
      />
    </Svg>
  );
}

/** Circular arrow — reset. */
export function RefreshIcon({ className }: IconProps) {
  return (
    <Svg className={className}>
      <path
        d="M19 12a7 7 0 1 1-2.1-5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M19.5 4v4.2h-4.2"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

/** Paperclip — attach. */
export function PaperclipIcon({ className }: IconProps) {
  return (
    <Svg className={className}>
      <path
        d="M17.5 9.3 10.8 16a3 3 0 0 1-4.2-4.2l7.4-7.4a4.5 4.5 0 0 1 6.4 6.4l-7.4 7.4a6 6 0 0 1-8.5-8.5l6.6-6.6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

/** Paper plane — send. */
export function SendIcon({ className }: IconProps) {
  return (
    <Svg className={className}>
      <path
        d="M21 3 3 10.4l7 2.6 2.6 7L21 3Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M10 13 21 3"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </Svg>
  );
}
