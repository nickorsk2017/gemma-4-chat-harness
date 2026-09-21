/** Format an epoch-millis timestamp as a fixed 24h `HH:MM` label.
 *
 * Deliberately arithmetic rather than `toLocaleTimeString`: the output must not
 * vary with the runtime locale, so a restored transcript renders identically
 * everywhere it is read. */
export function formatTime(epochMillis: number): string {
  const d = new Date(epochMillis);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}
