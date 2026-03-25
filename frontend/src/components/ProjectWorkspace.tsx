import type { ArtifactRole } from "../lib/artifactRoles";
import type { Workspace } from "../lib/types";

import DraftPanel from "./DraftPanel";
import EvidenceReviewPanel from "./EvidenceReviewPanel";
import ExportPanel from "./ExportPanel";
import FigureReviewPanel from "./FigureReviewPanel";
import OutlinePanel from "./OutlinePanel";
import QualitySummaryPanel from "./QualitySummaryPanel";
import UploadPanel from "./UploadPanel";
import { stageRunLabel, stageRunningLabel, stageIsBusy } from "../lib/stages";
import { useState } from "react";


type ProjectWorkspaceProps = {
  onDeleteArtifact: (artifactId: string) => Promise<void>;
  onUpdateArtifactRole: (artifactId: string, role: ArtifactRole) => Promise<void>;
  onRunExport: (mode: "draft" | "final") => Promise<void>;
  pendingStage: string | null;
  workspace: Workspace;
  onRunStageWithInput: (stage: string, input?: { mode?: string }) => Promise<void>;
  onSelectFigureAsset: (figureSpecId: string, figureAssetId: string) => Promise<void>;
  onUploadFiles: (uploads: Array<{ file: File; role: ArtifactRole }>) => Promise<void>;
  onRunStage: (stage: string) => Promise<void>;
  onSaveSection: (sectionId: string, content: string) => Promise<void>;
  onReviewSlot: (slotId: string, status: string, selectedReferenceIds?: string[]) => Promise<void>;
};


export default function ProjectWorkspace({
  onDeleteArtifact,
  onUpdateArtifactRole,
  onRunExport,
  pendingStage,
  workspace,
  onRunStageWithInput,
  onSelectFigureAsset,
  onUploadFiles,
  onRunStage,
  onSaveSection,
  onReviewSlot
}: ProjectWorkspaceProps) {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const runAllBusy = stageIsBusy("run_all", workspace.jobs, pendingStage);

  return (
    <main className="workspace">
      <div className="workspace-hero">
        <div>
          <p className="eyebrow">Workspace</p>
          <h2>{workspace.project.title}</h2>
        </div>
        <div className="workspace-hero-copy">
          <p>{workspace.project.objective || "No objective yet."}</p>
          <div className="workspace-hero-actions">
            <button className="primary-button" disabled={runAllBusy} onClick={() => onRunStage("run_all")} type="button">
              {runAllBusy ? stageRunningLabel("run_all") : stageRunLabel("run_all")}
            </button>
            <button className="ghost-button" onClick={() => setAdvancedOpen((current) => !current)} type="button">
              {advancedOpen ? "Hide Advanced" : "Advanced"}
            </button>
          </div>
        </div>
      </div>
      <div className="workspace-grid">
        <UploadPanel
          artifacts={workspace.artifacts}
          datasetProfile={workspace.dataset_profile}
          jobs={workspace.jobs}
          pendingStage={pendingStage}
          showManualControls={advancedOpen}
          onDeleteArtifact={onDeleteArtifact}
          onUpdateArtifactRole={onUpdateArtifactRole}
          onRunStage={onRunStage}
          onUploadFiles={onUploadFiles}
          project={workspace.project}
        />
        <OutlinePanel
          jobs={workspace.jobs}
          outline={workspace.outline}
          pendingStage={pendingStage}
          showManualControls={advancedOpen}
          onRunStage={onRunStage}
        />
        <DraftPanel
          draftSections={workspace.draft_sections}
          jobs={workspace.jobs}
          pendingStage={pendingStage}
          showManualControls={advancedOpen}
          onRunStage={onRunStage}
          onSaveSection={onSaveSection}
        />
        <EvidenceReviewPanel
          citationSlots={workspace.citation_slots}
          evidenceMatches={workspace.evidence_matches}
          jobs={workspace.jobs}
          pendingStage={pendingStage}
          showManualControls={advancedOpen}
          onReviewSlot={onReviewSlot}
          onRunStage={onRunStage}
          references={workspace.reference_records}
        />
        <QualitySummaryPanel
          jobs={workspace.jobs}
          pendingStage={pendingStage}
          qualityReport={workspace.quality_report}
          showManualControls={advancedOpen}
          onRunStage={onRunStage}
        />
        <FigureReviewPanel
          figureSpecs={workspace.figure_specs}
          jobs={workspace.jobs}
          onRunStage={() => onRunStageWithInput("figures")}
          onSelectFigureAsset={onSelectFigureAsset}
          pendingStage={pendingStage}
          showManualControls={advancedOpen}
        />
        <ExportPanel
          exportBundle={workspace.export_bundle}
          jobs={workspace.jobs}
          pendingStage={pendingStage}
          qualityReport={workspace.quality_report}
          onRunExport={onRunExport}
        />
      </div>
    </main>
  );
}
