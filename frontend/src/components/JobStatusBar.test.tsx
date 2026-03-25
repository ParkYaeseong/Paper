import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import JobStatusBar from "./JobStatusBar";


describe("JobStatusBar", () => {
  it("shows the active Run All substage when the job log includes one", () => {
    render(
      <JobStatusBar
        notice={{
          id: "job-1",
          stage: "run_all",
          status: "running",
          logText: "Running draft",
        }}
      />,
    );

    expect(screen.getByText("Running Draft")).toBeInTheDocument();
    expect(screen.getByText("Writing manuscript sections from the structured project profile.")).toBeInTheDocument();
  });

  it("keeps the failure log text when the job fails", () => {
    render(
      <JobStatusBar
        notice={{
          id: "job-2",
          stage: "run_all",
          status: "failed",
          logText: "PaperBanana failed",
        }}
      />,
    );

    expect(screen.getByText("Run All failed")).toBeInTheDocument();
    expect(screen.getByText("PaperBanana failed")).toBeInTheDocument();
  });
});
