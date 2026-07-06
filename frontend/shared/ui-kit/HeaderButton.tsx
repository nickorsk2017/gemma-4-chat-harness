"use client";

interface HeaderButtonProps {
  /** Visible label of the action. */
  label: string;
  onClick: () => void;
  disabled?: boolean;
  /** Accessible name when the label alone is not descriptive enough. */
  ariaLabel?: string;
}

/** Presentational compact action button for header bars. No store access. */
export function HeaderButton({
  label,
  onClick,
  disabled = false,
  ariaLabel,
}: HeaderButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel ?? label}
      className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-gray-100"
    >
      {label}
    </button>
  );
}
