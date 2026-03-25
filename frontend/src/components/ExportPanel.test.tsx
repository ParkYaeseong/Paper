import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ExportPanel from "./ExportPanel";


describe("ExportPanel", () => {
  it("disables export while the export stage is active and shows the last failure", () => {
    render(
      <ExportPanel
        exportBundle={null}
        jobs={[
          {
            id: "job-1",
            stage: "export",
            status: "running",
            payload_json: null,
            result_json: null,
            log_text: "",
            started_at: "2026-03-25T00:00:00Z",
            finished_at: null,
            created_at: "2026-03-25T00:00:00Z",
            updated_at: "2026-03-25T00:00:00Z",
          },
          {
            id: "job-2",
            stage: "ground",
            status: "failed",
            payload_json: null,
            result_json: null,
            log_text: "grounding failed",
            started_at: "2026-03-25T00:00:00Z",
            finished_at: "2026-03-25T00:00:02Z",
            created_at: "2026-03-25T00:00:00Z",
            updated_at: "2026-03-25T00:00:02Z",
          },
        ]}
        pendingStage={null}
        qualityReport={{
          id: "quality-1",
          version: 1,
          critical_issues_json: [{ code: "manual_review_marker", message: "Manual review remains." }],
          warnings_json: [],
          recommended_actions_json: [],
          submission_ready: false,
          created_at: "2026-03-25T00:00:00Z",
        }}
        onRunExport={vi.fn()}
      />,
    );

    expect(screen.getAllByRole("button", { name: "Export Running..." })).toHaveLength(2);
    expect(screen.getByText("grounding failed")).toBeInTheDocument();
  });
});
