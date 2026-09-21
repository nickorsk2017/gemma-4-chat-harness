import { Fragment } from "react";
import {
  parseBlocks,
  type BlockNode,
  type ListItem,
} from "@/shared/ui-kit/markdown/parseBlocks";
import {
  parseInline,
  type InlineNode,
} from "@/shared/ui-kit/markdown/parseInline";

interface MarkdownProps {
  /** Raw Markdown text. A partial (streamed) prefix is safe to pass. */
  source: string;
}

const HEADING_SIZE = [
  "text-base",
  "text-base",
  "text-sm",
  "text-sm",
  "text-sm",
  "text-sm",
];

function Inline({ nodes }: { nodes: InlineNode[] }) {
  return (
    <>
      {nodes.map((node, i) => {
        switch (node.type) {
          case "text":
            return <Fragment key={i}>{node.value}</Fragment>;
          case "code":
            return (
              <code
                key={i}
                className="rounded bg-black/10 px-1 py-0.5 font-mono text-[0.9em]"
              >
                {node.value}
              </code>
            );
          case "bold":
            return (
              <strong key={i} className="font-semibold">
                <Inline nodes={node.children} />
              </strong>
            );
          case "italic":
            return (
              <em key={i}>
                <Inline nodes={node.children} />
              </em>
            );
          case "link":
            return (
              <a
                key={i}
                href={node.href}
                target="_blank"
                rel="noopener noreferrer"
                className="underline underline-offset-2"
              >
                <Inline nodes={node.children} />
              </a>
            );
        }
      })}
    </>
  );
}

function Items({ items, ordered }: { items: ListItem[]; ordered: boolean }) {
  const Tag = ordered ? "ol" : "ul";
  return (
    <Tag
      className={[
        "my-1.5 space-y-1 pl-5",
        ordered ? "list-decimal" : "list-disc",
      ].join(" ")}
    >
      {items.map((item, i) => (
        <li key={i}>
          <Inline nodes={parseInline(item.text)} />
          {item.children.length > 0 && (
            <Items items={item.children} ordered={ordered} />
          )}
        </li>
      ))}
    </Tag>
  );
}

function Block({ node }: { node: BlockNode }) {
  switch (node.type) {
    case "heading": {
      const Tag = `h${node.level}` as "h1";
      return (
        <Tag
          className={`mt-3 mb-1 font-semibold first:mt-0 ${HEADING_SIZE[node.level - 1]}`}
        >
          <Inline nodes={parseInline(node.text)} />
        </Tag>
      );
    }
    case "paragraph":
      return (
        <p className="my-1.5 whitespace-pre-wrap first:mt-0 last:mb-0">
          <Inline nodes={parseInline(node.text)} />
        </p>
      );
    case "code":
      return (
        <pre className="my-2 overflow-x-auto rounded-control bg-black/10 p-2.5 first:mt-0 last:mb-0">
          <code className="font-mono text-xs">{node.value}</code>
        </pre>
      );
    case "list":
      return <Items items={node.items} ordered={node.ordered} />;
    case "quote":
      return (
        <blockquote className="my-2 border-l-2 border-hairline pl-3 text-muted">
          {node.children.map((child, i) => (
            <Block key={i} node={child} />
          ))}
        </blockquote>
      );
    case "rule":
      return <hr className="my-3 border-hairline" />;
  }
}

/** Renders Markdown as React elements. No raw HTML is ever injected: content that
 * looks like HTML is escaped by React and rendered as text. */
export function Markdown({ source }: MarkdownProps) {
  const blocks = parseBlocks(source);
  return (
    <div className="break-words">
      {blocks.map((node, i) => (
        <Block key={i} node={node} />
      ))}
    </div>
  );
}
