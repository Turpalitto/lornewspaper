import { render, screen } from "@testing-library/react";
import { Badge } from "@/components/ui/badge";
import { describe, it, expect } from "vitest";

describe("Badge", () => {
  it("renders text", () => {
    render(<Badge>New</Badge>);
    expect(screen.getByText("New")).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    render(<Badge variant="destructive">Error</Badge>);
    const badge = screen.getByText("Error");
    expect(badge.className).toContain("bg-destructive");
  });
});
