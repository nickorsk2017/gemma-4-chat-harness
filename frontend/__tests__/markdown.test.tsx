import { render, screen } from "@testing-library/react";
import { Markdown } from "@/shared/ui-kit/Markdown";
import { MessageBubble } from "@/shared/ui-kit/MessageBubble";

describe("Markdown", () => {
  it("renders headings, bold and bullet lists without markup characters", () => {
    const { container } = render(
      <Markdown source={"# Title\n\nSome **bold** text\n\n* one\n* two"} />,
    );

    expect(container.querySelector("h1")).toHaveTextContent("Title");
    expect(container.querySelector("strong")).toHaveTextContent("bold");
    expect(container.querySelectorAll("ul > li")).toHaveLength(2);
    expect(container.textContent).not.toMatch(/[*#]/);
  });

  it("renders a fenced code block verbatim", () => {
    const { container } = render(
      <Markdown source={"```ts\nconst a = **1**;\n```"} />,
    );

    const code = container.querySelector("pre > code");
    expect(code).toHaveTextContent("const a = **1**;");
    expect(container.querySelector("strong")).toBeNull();
  });

  it("renders a truncated prefix without throwing", () => {
    expect(() => render(<Markdown source="**bo" />)).not.toThrow();
    expect(screen.getByText("**bo")).toBeInTheDocument();
  });

  it("rejects unsafe link schemes and hardens safe ones", () => {
    const { container } = render(
      <Markdown
        source={"[evil](javascript:alert(1)) and [ok](https://example.com)"}
      />,
    );

    const links = container.querySelectorAll("a");
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAttribute("href", "https://example.com");
    expect(links[0]).toHaveAttribute("rel", "noopener noreferrer");
    expect(container.textContent).toContain("[evil](javascript:alert(1))");
  });

  it("does not inject raw HTML from the content", () => {
    const { container } = render(
      <Markdown source={"<script>alert(1)</script>"} />,
    );

    expect(container.querySelector("script")).toBeNull();
    expect(container.textContent).toContain("<script>alert(1)</script>");
  });
});

describe("MessageBubble", () => {
  it("keeps user messages as plain text", () => {
    const { container } = render(
      <MessageBubble role="user" content="**not bold** and * not a list" />,
    );

    expect(container.querySelector("strong")).toBeNull();
    expect(container.querySelector("ul")).toBeNull();
    expect(container.textContent).toContain("**not bold** and * not a list");
  });

  it("renders assistant messages as markdown", () => {
    const { container } = render(
      <MessageBubble role="assistant" content="**bold**" />,
    );

    expect(container.querySelector("strong")).toHaveTextContent("bold");
  });
});
