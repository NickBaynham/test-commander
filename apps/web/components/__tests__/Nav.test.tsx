import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Nav from "../Nav";

describe("Nav", () => {
  it("links every console page", () => {
    render(<Nav />);
    for (const label of [
      "Dashboard",
      "Quality Report",
      "Journal",
      "Sessions",
      "Requirements",
      "Test Runs",
      "Evidence",
      "Chat",
      "Settings",
    ]) {
      expect(screen.getByText(label)).toBeTruthy();
    }
  });
});
