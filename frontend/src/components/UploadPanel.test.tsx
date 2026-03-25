import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import UploadPanel from "./UploadPanel";


describe("UploadPanel", () => {
  it("shows uploaded artifacts immediately before ingest runs", () => {
    render(
      <UploadPanel
        artifacts={[
          {
            id: "artifact-1",
            project_id: "project-1",
            kind: "upload",
            filename: "results.csv",
            content_type: "text/csv",
            storage_path: "/tmp/results.csv",
            size_bytes: 42,
            sha256: "abc123",
            created_at: "2026-03-25T00:00:00Z",
            updated_at: "2026-03-25T00:00:00Z",
          },
        ]}
        datasetProfile={null}
        jobs={[]}
        onRunStage={vi.fn().mockResolvedValue(undefined)}
        onUploadFiles={vi.fn().mockResolvedValue(undefined)}
        project={{
          id: "project-1",
          title: "Protein pipeline manuscript",
          objective: "Describe the uploaded workflow materials.",
          status: "draft",
          owner_sub: "user-1",
          owner_username: "tester",
          created_at: "2026-03-25T00:00:00Z",
          updated_at: "2026-03-25T00:00:00Z",
        }}
      />,
    );

    expect(screen.getAllByText("1")).toHaveLength(2);
    expect(screen.getByText("results.csv")).toBeInTheDocument();
    expect(screen.getByText(/run ingest to summarize/i)).toBeInTheDocument();
  });
});
