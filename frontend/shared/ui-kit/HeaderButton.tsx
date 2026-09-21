"use client";

interface HeaderButtonProps {
  /** Visible label of the action. */
  label: string;
  onClick: () => void;
  disabled?: boolean;
  /** Accessible name when the label alone is not descriptive enough. */
  ariaLabel?: string;
  /** Decorative glyph rendered before the label. */
  icon?: React.ReactNode;
}

/** Presentational compact action button for header bars. No store access. */
export function HeaderButton({
  label,
  onClick,
  disabled = false,
  ariaLabel,
  icon,
}: HeaderButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel ?? label}
      className="flex items-center gap-2 rounded-full border border-hairline px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-page disabled:cursor-not-allowed disabled:opacity-50"
    >
      {icon}
      {label}
    </button>
  );
}
