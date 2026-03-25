import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import QualitySummaryPanel from "./QualitySummaryPanel";


describe("QualitySummaryPanel", () => {
  it("shows critical and warning counts with recommended actions", () => {
    render(
      <QualitySummaryPanel
        qualityReport={{
          id: "quality-1",
          version: 1,
          critical_issues_json: [{ code: "unresolved_figure_placeholder", message: "Figure 1 needs a selected asset." }],
          warnings_json: [{ code: "generic_results_section", message: "Results are too generic." }],
          recommended_actions_json: ["Generate or select figure candidates for every figure placeholder."],
          submission_ready: false,
          created_at: "2026-03-25T00:00:00Z",
        }}
      />,
    );

    expect(screen.getByText("1 critical issue")).toBeInTheDocument();
    expect(screen.getByText("1 warning")).toBeInTheDocument();
    expect(screen.getByText("Figure 1 needs a selected asset.")).toBeInTheDocument();
    expect(screen.getByText("Generate or select figure candidates for every figure placeholder.")).toBeInTheDocument();
    expect(screen.getByText("Final export blocked")).toBeInTheDocument();
  });
});
