import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import FigureReviewPanel from "./FigureReviewPanel";


describe("FigureReviewPanel", () => {
  it("renders figure candidates and allows selecting a candidate", async () => {
    const onSelectFigureAsset = vi.fn().mockResolvedValue(undefined);

    render(
      <FigureReviewPanel
        figureSpecs={[
          {
            id: "figure-spec-1",
            section_key: "methods",
            figure_key: "FIGURE_1",
            figure_number: 1,
            caption_draft: "Overall workflow architecture.",
            source_excerpt: "The workflow combines upload, orchestration, and review.",
            visual_intent: "Show the overall workflow.",
            status: "generated",
            selected_figure_asset_id: "figure-asset-1",
            assets: [
              {
                id: "figure-asset-1",
                artifact_id: "artifact-1",
                provider: "paperbanana",
                status: "generated",
                selected: true,
                filename: "figure_1_a.png",
                storage_path: "/tmp/figure_1_a.png",
                download_url: "/api/projects/project-1/artifacts/artifact-1/download",
                created_at: "2026-03-25T00:00:00Z",
                updated_at: "2026-03-25T00:00:00Z",
              },
              {
                id: "figure-asset-2",
                artifact_id: "artifact-2",
                provider: "paperbanana",
                status: "generated",
                selected: false,
                filename: "figure_1_b.png",
                storage_path: "/tmp/figure_1_b.png",
                download_url: "/api/projects/project-1/artifacts/artifact-2/download",
                created_at: "2026-03-25T00:00:00Z",
                updated_at: "2026-03-25T00:00:00Z",
              },
            ],
          },
        ]}
        onRunStage={vi.fn().mockResolvedValue(undefined)}
        onSelectFigureAsset={onSelectFigureAsset}
        showManualControls
      />,
    );

    expect(screen.getByText("Figure 1")).toBeInTheDocument();
    expect(screen.getByText("Overall workflow architecture.")).toBeInTheDocument();
    expect(screen.getByText("Selected")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Select figure_1_b.png" }));

    expect(onSelectFigureAsset).toHaveBeenCalledWith("figure-spec-1", "figure-asset-2");
  });
});
