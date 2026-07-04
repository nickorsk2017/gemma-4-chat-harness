import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

describe("Hello World page", () => {
  it("renders the Hello World heading", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: /hello world/i })
    ).toBeInTheDocument();
  });
});
