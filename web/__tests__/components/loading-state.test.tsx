import { render } from "@testing-library/react";
import { LoadingState } from "@/components/shared/loading-state";
import { describe, it, expect } from "vitest";

describe("LoadingState", () => {
  it("renders specified number of skeleton groups", () => {
    const { container } = render(<LoadingState count={5} />);
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBe(15);
  });

  it("renders default count of 3", () => {
    const { container } = render(<LoadingState />);
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBe(9);
  });
});
