import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import FigureReviewPanel from "./FigureReviewPanel";


describe("FigureReviewPanel", () => {
  it("renders figure handoff content and copies caption and method text", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });

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
            method_section_content: "### Methods\n\nThe workflow combines upload, orchestration, and review.",
            visual_intent: "Show the overall workflow.",
            status: "prepared",
            selected_figure_asset_id: null,
            assets: [],
          },
        ]}
        onRunStage={vi.fn().mockResolvedValue(undefined)}
        showManualControls
      />,
    );

    expect(screen.getByText("Figure 1")).toBeInTheDocument();
    expect(screen.getAllByText("Overall workflow architecture.")).toHaveLength(2);
    expect(
      screen.getByText((content) => content.includes("### Methods") && content.includes("The workflow combines upload, orchestration, and review.")),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Copy method content" }));
    fireEvent.click(screen.getByRole("button", { name: "Copy figure caption" }));

    expect(writeText).toHaveBeenNthCalledWith(1, "### Methods\n\nThe workflow combines upload, orchestration, and review.");
    expect(writeText).toHaveBeenNthCalledWith(2, "Overall workflow architecture.");
  });

  it("shows the new text handoff empty state", () => {
    render(
      <FigureReviewPanel
        figureSpecs={[]}
        onRunStage={vi.fn().mockResolvedValue(undefined)}
        showManualControls
      />,
    );

    expect(screen.getByText("No figure handoff text yet. Run All or the figure stage to prepare PaperBanana-ready caption and method content.")).toBeInTheDocument();
  });
});
