import type { Workspace } from "../lib/types";

import DraftPanel from "./DraftPanel";
import EvidenceReviewPanel from "./EvidenceReviewPanel";
import ExportPanel from "./ExportPanel";
import OutlinePanel from "./OutlinePanel";
import UploadPanel from "./UploadPanel";


type ProjectWorkspaceProps = {
  workspace: Workspace;
  onUploadFiles: (files: File[]) => Promise<void>;
  onRunStage: (stage: string) => Promise<void>;
  onSaveSection: (sectionId: string, content: string) => Promise<void>;
  onReviewSlot: (slotId: string, status: string, selectedReferenceIds?: string[]) => Promise<void>;
};


export default function ProjectWorkspace({
  workspace,
  onUploadFiles,
  onRunStage,
  onSaveSection,
  onReviewSlot
}: ProjectWorkspaceProps) {
  return (
    <main className="workspace">
      <div className="workspace-hero">
        <div>
          <p className="eyebrow">Workspace</p>
          <h2>{workspace.project.title}</h2>
        </div>
        <p>{workspace.project.objective || "No objective yet."}</p>
      </div>
      <div className="workspace-grid">
        <UploadPanel
          datasetProfile={workspace.dataset_profile}
          onRunStage={onRunStage}
          onUploadFiles={onUploadFiles}
          project={workspace.project}
        />
        <OutlinePanel outline={workspace.outline} onRunStage={onRunStage} />
        <DraftPanel
          draftSections={workspace.draft_sections}
          onRunStage={onRunStage}
          onSaveSection={onSaveSection}
        />
        <EvidenceReviewPanel
          citationSlots={workspace.citation_slots}
          evidenceMatches={workspace.evidence_matches}
          onReviewSlot={onReviewSlot}
          onRunStage={onRunStage}
          references={workspace.reference_records}
        />
        <ExportPanel
          exportBundle={workspace.export_bundle}
          jobs={workspace.jobs}
          onRunStage={onRunStage}
        />
      </div>
    </main>
  );
}
