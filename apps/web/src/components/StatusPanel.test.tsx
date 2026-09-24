import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { getDictionary } from "@/lib/i18n";

import { StatusPanel } from "./StatusPanel";

vi.mock("server-only", () => ({}));

describe("StatusPanel", () => {
  const dict = getDictionary("en");

  it("shows the API as unreachable without crashing", () => {
    render(<StatusPanel result={{ reachable: false }} dict={dict} />);
    expect(screen.getByRole("status")).toHaveTextContent("API unreachable");
  });

  it("reports missing AI providers without marking the system unavailable", () => {
    render(
      <StatusPanel
        result={{ reachable: true, readiness: { status: "ready", database: "ok", queue: "ok", ai_providers_configured: [] } }}
        dict={dict}
      />,
    );
    expect(screen.getByTestId("overall-status")).toHaveTextContent("Ready");
    expect(screen.getByText("none configured")).toBeInTheDocument();
  });
});
