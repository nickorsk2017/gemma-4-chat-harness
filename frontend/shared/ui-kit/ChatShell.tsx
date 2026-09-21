interface ChatShellProps {
  header: React.ReactNode;
  footer: React.ReactNode;
  children: React.ReactNode;
}

/** Page shell: a centered card floating on the neutral page background.
 * Holds the header, the scrollable transcript and the composer. */
export function ChatShell({ header, footer, children }: ChatShellProps) {
  return (
    <div className="flex h-dvh w-full justify-center bg-page p-3 sm:p-6">
      <div className="flex h-full w-full max-w-3xl flex-col overflow-hidden rounded-card border border-hairline bg-surface shadow-card">
        <header className="border-b border-hairline px-5 py-4">{header}</header>
        <main className="flex-1 space-y-5 overflow-y-auto px-5 py-6">
          {children}
        </main>
        <footer className="px-4 pb-4 pt-2">{footer}</footer>
      </div>
    </div>
  );
}
