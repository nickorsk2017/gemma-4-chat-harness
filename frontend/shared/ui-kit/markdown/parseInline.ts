/** Inline Markdown grammar: code, links, bold, italic. Pure, no React. */

export type InlineNode =
  | { type: "text"; value: string }
  | { type: "code"; value: string }
  | { type: "bold"; children: InlineNode[] }
  | { type: "italic"; children: InlineNode[] }
  | { type: "link"; href: string; children: InlineNode[] };

const SAFE_SCHEME = /^(https?:|mailto:)/i;
const ANY_SCHEME = /^[a-z][a-z0-9+.-]*:/i;

/** A URL is safe when it carries an allowed scheme or no scheme at all. */
export function isSafeHref(href: string): boolean {
  const value = href.trim();
  if (value === "") return false;
  if (SAFE_SCHEME.test(value)) return true;
  return !ANY_SCHEME.test(value);
}

function push(nodes: InlineNode[], value: string): void {
  const last = nodes[nodes.length - 1];
  if (last && last.type === "text") last.value += value;
  else nodes.push({ type: "text", value });
}

function findClosing(src: string, from: number, marker: string): number {
  const at = src.indexOf(marker, from);
  return at === -1 ? -1 : at;
}

/** Parses inline markup. Unmatched delimiters are emitted literally, so a
 * truncated prefix (mid-syntax) is always renderable. */
export function parseInline(src: string): InlineNode[] {
  const out: InlineNode[] = [];
  let i = 0;

  while (i < src.length) {
    const rest = src.slice(i);

    if (rest.startsWith("`")) {
      const end = findClosing(src, i + 1, "`");
      if (end !== -1) {
        out.push({ type: "code", value: src.slice(i + 1, end) });
        i = end + 1;
        continue;
      }
    }

    if (rest.startsWith("[")) {
      const close = findClosing(src, i + 1, "](");
      const paren = close === -1 ? -1 : findClosing(src, close + 2, ")");
      if (close !== -1 && paren !== -1) {
        const label = src.slice(i + 1, close);
        const href = src.slice(close + 2, paren);
        if (isSafeHref(href)) {
          out.push({ type: "link", href: href.trim(), children: parseInline(label) });
        } else {
          push(out, src.slice(i, paren + 1));
        }
        i = paren + 1;
        continue;
      }
    }

    for (const marker of ["**", "__"]) {
      if (rest.startsWith(marker)) {
        const end = findClosing(src, i + marker.length, marker);
        if (end !== -1) {
          out.push({ type: "bold", children: parseInline(src.slice(i + marker.length, end)) });
          i = end + marker.length;
        }
        break;
      }
    }
    if (i < src.length && src.slice(i) !== rest) continue;

    for (const marker of ["*", "_"]) {
      if (rest.startsWith(marker)) {
        const end = findClosing(src, i + 1, marker);
        if (end !== -1 && end > i + 1) {
          out.push({ type: "italic", children: parseInline(src.slice(i + 1, end)) });
          i = end + 1;
        }
        break;
      }
    }
    if (i < src.length && src.slice(i) !== rest) continue;

    push(out, src[i]);
    i += 1;
  }

  return out;
}
