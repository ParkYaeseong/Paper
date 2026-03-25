import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import UploadPanel from "./UploadPanel";


describe("UploadPanel", () => {
  const project = {
    id: "project-1",
    title: "Protein pipeline manuscript",
    objective: "Describe the uploaded workflow materials.",
    status: "draft",
    owner_sub: "user-1",
    owner_username: "tester",
    created_at: "2026-03-25T00:00:00Z",
    updated_at: "2026-03-25T00:00:00Z",
  };

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
            role: "results_table",
            metadata_json: { role: "results_table" },
            created_at: "2026-03-25T00:00:00Z",
            updated_at: "2026-03-25T00:00:00Z",
          },
        ]}
        datasetProfile={null}
        jobs={[]}
        pendingStage={null}
        showManualControls
        onDeleteArtifact={vi.fn().mockResolvedValue(undefined)}
        onUpdateArtifactRole={vi.fn().mockResolvedValue(undefined)}
        onRunStage={vi.fn().mockResolvedValue(undefined)}
        onUploadFiles={vi.fn().mockResolvedValue(undefined)}
        project={project}
      />,
    );

    expect(screen.getAllByText("1")).toHaveLength(2);
    expect(screen.getByText("results.csv")).toBeInTheDocument();
    expect(screen.getByText(/run ingest to summarize/i)).toBeInTheDocument();
  });

  it("calls the delete handler for an uploaded artifact", async () => {
    const onDeleteArtifact = vi.fn().mockResolvedValue(undefined);

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
            role: "results_table",
            metadata_json: { role: "results_table" },
            created_at: "2026-03-25T00:00:00Z",
            updated_at: "2026-03-25T00:00:00Z",
          },
        ]}
        datasetProfile={null}
        jobs={[]}
        pendingStage={null}
        showManualControls
        onDeleteArtifact={onDeleteArtifact}
        onUpdateArtifactRole={vi.fn().mockResolvedValue(undefined)}
        onRunStage={vi.fn().mockResolvedValue(undefined)}
        onUploadFiles={vi.fn().mockResolvedValue(undefined)}
        project={project}
      />,
    );

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Delete results.csv" }));
    });

    expect(onDeleteArtifact).toHaveBeenCalledWith("artifact-1");
  });

  it("lets users choose file roles before upload", async () => {
    const onUploadFiles = vi.fn().mockResolvedValue(undefined);

    render(
      <UploadPanel
        artifacts={[]}
        datasetProfile={null}
        jobs={[]}
        pendingStage={null}
        showManualControls
        onDeleteArtifact={vi.fn().mockResolvedValue(undefined)}
        onUpdateArtifactRole={vi.fn().mockResolvedValue(undefined)}
        onRunStage={vi.fn().mockResolvedValue(undefined)}
        onUploadFiles={onUploadFiles}
        project={project}
      />,
    );

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const briefFile = new File(["# Brief"], "project_intake.md", { type: "text/markdown" });
    const resultsFile = new File(["metric,value\nsuccess_rate,0.82\n"], "results.csv", { type: "text/csv" });

    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [briefFile, resultsFile] } });
    });

    const pendingRoleSelects = screen.getAllByRole("combobox", { name: /role for/i });
    expect(pendingRoleSelects).toHaveLength(2);
    expect((pendingRoleSelects[0] as HTMLSelectElement).value).toBe("supporting_doc");
    expect((pendingRoleSelects[1] as HTMLSelectElement).value).toBe("results_table");

    await act(async () => {
      fireEvent.change(pendingRoleSelects[0], { target: { value: "narrative_brief" } });
      fireEvent.click(screen.getByRole("button", { name: "Upload Selected Files" }));
    });

    expect(onUploadFiles).toHaveBeenCalledWith([
      { file: briefFile, role: "narrative_brief" },
      { file: resultsFile, role: "results_table" },
    ]);
  });

  it("lets users update an uploaded artifact role and marks ingest as stale", async () => {
    const onUpdateArtifactRole = vi.fn().mockResolvedValue(undefined);

    render(
      <UploadPanel
        artifacts={[
          {
            id: "artifact-1",
            project_id: "project-1",
            kind: "upload",
            filename: "project_intake.md",
            content_type: "text/markdown",
            storage_path: "/tmp/project_intake.md",
            size_bytes: 120,
            sha256: "brief-1",
            role: "supporting_doc",
            metadata_json: { role: "supporting_doc" },
            created_at: "2026-03-25T00:00:00Z",
            updated_at: "2026-03-25T00:00:00Z",
          },
        ]}
        datasetProfile={{
          id: "profile-1",
          version: 1,
          summary_json: {
            dataset_summary: {
              artifact_count: 1,
              table_count: 0,
              source_artifacts: [
                {
                  artifact_id: "artifact-1",
                  filename: "project_intake.md",
                  role: "results_table",
                  sha256: "brief-1",
                },
              ],
            },
          },
        }}
        jobs={[]}
        pendingStage={null}
        showManualControls
        onDeleteArtifact={vi.fn().mockResolvedValue(undefined)}
        onUpdateArtifactRole={onUpdateArtifactRole}
        onRunStage={vi.fn().mockResolvedValue(undefined)}
        onUploadFiles={vi.fn().mockResolvedValue(undefined)}
        project={project}
      />,
    );

    expect(screen.getByText(/run ingest again to refresh the project profile/i)).toBeInTheDocument();

    const roleSelect = screen.getByRole("combobox", { name: "Uploaded role for project_intake.md" });

    await act(async () => {
      fireEvent.change(roleSelect, { target: { value: "narrative_brief" } });
    });

    expect(onUpdateArtifactRole).toHaveBeenCalledWith("artifact-1", "narrative_brief");
  });
});
