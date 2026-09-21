interface BadgeProps {
  label: string;
}

/** Small rounded accent tag used next to a title. */
export function Badge({ label }: BadgeProps) {
  return (
    <span className="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-semibold text-accent">
      {label}
    </span>
  );
}
