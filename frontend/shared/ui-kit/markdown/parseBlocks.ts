/** Block-level Markdown grammar. Pure, no React. */

export interface ListItem {
  text: string;
  children: ListItem[];
}

export type BlockNode =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "code"; language: string; value: string }
  | { type: "list"; ordered: boolean; items: ListItem[] }
  | { type: "quote"; children: BlockNode[] }
  | { type: "rule" };

const HEADING = /^(#{1,6})\s+(.*)$/;
const RULE = /^\s*(?:-{3,}|\*{3,}|_{3,})\s*$/;
const LIST_ITEM = /^(\s*)(?:([-*+])|(\d+)[.)])\s+(.*)$/;
const FENCE = /^\s*```(.*)$/;

/** Nests flat list rows by indent width (two spaces per level). */
function nest(rows: { indent: number; text: string }[]): ListItem[] {
  const root: ListItem[] = [];
  const stack: { indent: number; items: ListItem[] }[] = [{ indent: -1, items: root }];

  for (const row of rows) {
    while (stack.length > 1 && row.indent <= stack[stack.length - 1].indent) stack.pop();
    const item: ListItem = { text: row.text, children: [] };
    stack[stack.length - 1].items.push(item);
    stack.push({ indent: row.indent, items: item.children });
  }
  return root;
}

/** Parses Markdown into blocks. Anything unrecognised becomes a paragraph, and an
 * unterminated code fence runs to the end of input (correct for a streamed prefix). */
export function parseBlocks(src: string): BlockNode[] {
  const lines = src.replace(/\r\n/g, "\n").split("\n");
  const out: BlockNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim() === "") {
      i += 1;
      continue;
    }

    const fence = FENCE.exec(line);
    if (fence) {
      const body: string[] = [];
      i += 1;
      while (i < lines.length && !FENCE.test(lines[i])) {
        body.push(lines[i]);
        i += 1;
      }
      if (i < lines.length) i += 1;
      out.push({ type: "code", language: fence[1].trim(), value: body.join("\n") });
      continue;
    }

    if (RULE.test(line)) {
      out.push({ type: "rule" });
      i += 1;
      continue;
    }

    const heading = HEADING.exec(line);
    if (heading) {
      out.push({ type: "heading", level: heading[1].length, text: heading[2].trim() });
      i += 1;
      continue;
    }

    if (/^\s*>\s?/.test(line)) {
      const body: string[] = [];
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
        body.push(lines[i].replace(/^\s*>\s?/, ""));
        i += 1;
      }
      out.push({ type: "quote", children: parseBlocks(body.join("\n")) });
      continue;
    }

    const first = LIST_ITEM.exec(line);
    if (first) {
      const ordered = first[3] !== undefined;
      const rows: { indent: number; text: string }[] = [];
      while (i < lines.length) {
        const match = LIST_ITEM.exec(lines[i]);
        if (!match) break;
        rows.push({ indent: match[1].length, text: match[4] });
        i += 1;
      }
      out.push({ type: "list", ordered, items: nest(rows) });
      continue;
    }

    const body: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !FENCE.test(lines[i]) &&
      !RULE.test(lines[i]) &&
      !HEADING.test(lines[i]) &&
      !LIST_ITEM.test(lines[i]) &&
      !/^\s*>\s?/.test(lines[i])
    ) {
      body.push(lines[i].trim());
      i += 1;
    }
    out.push({ type: "paragraph", text: body.join("\n") });
  }

  return out;
}
