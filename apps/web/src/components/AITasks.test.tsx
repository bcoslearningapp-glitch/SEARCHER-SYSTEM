import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { getDictionary } from "@/lib/i18n";
import type { AIProfile, Job } from "@/lib/types";

import { AITasks } from "./AITasks";

vi.mock("@/app/actions", () => ({ launchAITask: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

const ai = getDictionary("en").ai;
const mock: AIProfile = { name: "mock", provider: "mock", model: "m", local: true, configured: true, default: true };
const job = (overrides: Partial<Job>): Job => ({
  id: "j1",
  kind: "orchestrator.draft_problem_frame",
  state: "SUCCEEDED",
  project_id: "p1",
  params: {},
  result: null,
  failure_kind: null,
  error: null,
  created_at: "2026-09-24T00:00:00Z",
  finished_at: null,
  ...overrides,
});
const launchers = [{ task: "draft_problem_frame", label: ai.draftFrame }];

describe("AITasks", () => {
  afterEach(cleanup);

  it("keeps the project usable and says so when no provider is configured", () => {
    render(<AITasks ai={ai} projectId="p1" profiles={[{ ...mock, configured: false }]} jobs={[]} launchers={launchers} />);
    expect(screen.getByTestId("ai-unavailable")).toHaveTextContent("No AI provider is configured");
    expect(screen.queryByRole("button", { name: ai.draftFrame })).not.toBeInTheDocument();
  });

  it("offers launch buttons when a provider is configured", () => {
    render(<AITasks ai={ai} projectId="p1" profiles={[mock]} jobs={[]} launchers={launchers} />);
    expect(screen.getByRole("button", { name: ai.draftFrame })).toBeInTheDocument();
    expect(screen.getByText(ai.noTasks)).toBeInTheDocument();
  });

  it("explains a provider failure as not being evidence of absence", () => {
    render(
      <AITasks
        ai={ai}
        projectId="p1"
        profiles={[mock]}
        jobs={[job({ state: "FAILED", failure_kind: "PROVIDER_ERROR", error: "raw provider text" })]}
        launchers={launchers}
      />,
    );
    const item = screen.getByTestId("ai-task");
    expect(item).toHaveTextContent("Draft Problem Frame");
    expect(item).toHaveTextContent("does not mean no evidence exists");
    expect(item).not.toHaveTextContent("raw provider text");
  });

  it("shows budget exhaustion as a resource stop", () => {
    render(
      <AITasks
        ai={ai}
        projectId="p1"
        profiles={[mock]}
        jobs={[job({ state: "FAILED", failure_kind: "STOPPED_RESOURCE_CONSTRAINT", error: "budget" })]}
        launchers={launchers}
      />,
    );
    expect(screen.getByTestId("ai-task")).toHaveTextContent(ai.budgetStop);
  });
});
