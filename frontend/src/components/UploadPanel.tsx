import { useRef, useState } from "react";

import { stageIsBusy, stageRunLabel, stageRunningLabel } from "../lib/stages";
import type { Artifact, DatasetProfile, JobRun, Project } from "../lib/types";


type UploadPanelProps = {
  artifacts: Artifact[];
  project: Project;
  datasetProfile: DatasetProfile;
  jobs: JobRun[];
  pendingStage: string | null;
  showManualControls: boolean;
  onDeleteArtifact: (artifactId: string) => Promise<void>;
  onUploadFiles: (files: File[]) => Promise<void>;
  onRunStage: (stage: string) => Promise<void>;
};


export default function UploadPanel({
  artifacts,
  project,
  datasetProfile,
  jobs,
  pendingStage,
  showManualControls,
  onDeleteArtifact,
  onUploadFiles,
  onRunStage,
}: UploadPanelProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [deletingArtifactId, setDeletingArtifactId] = useState<string | null>(null);
  const summary = datasetProfile?.summary_json?.dataset_summary as
    | { artifact_count?: number; table_count?: number }
    | undefined;
  const artifactCount = artifacts.length;
  const inferredTableCount = artifacts.filter((artifact) => artifact.filename.toLowerCase().endsWith(".csv")).length;
  const ingestOutOfDate = Boolean(
    datasetProfile
      && (
        summary?.artifact_count !== artifactCount
        || summary?.table_count !== inferredTableCount
      ),
  );
  const tableCount = ingestOutOfDate ? inferredTableCount : (summary?.table_count ?? inferredTableCount);
  const visibleArtifacts = artifacts;
  const ingestBusy = stageIsBusy("ingest", jobs, pendingStage);

  async function handleUpload() {
    if (!files.length) return;
    await onUploadFiles(files);
    setFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  async function handleDeleteArtifact(artifactId: string) {
    setDeletingArtifactId(artifactId);
    try {
      await onDeleteArtifact(artifactId);
    } finally {
      setDeletingArtifactId(null);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Project Intake</p>
          <h3>Upload</h3>
        </div>
        {showManualControls ? (
          <button className="secondary-button" disabled={ingestBusy} onClick={() => onRunStage("ingest")} type="button">
            {ingestBusy ? stageRunningLabel("ingest") : stageRunLabel("ingest")}
          </button>
        ) : null}
      </div>
      <p className="panel-copy">{project.objective || "Add an objective to anchor the planning stage."}</p>
      <input
        ref={fileInputRef}
        multiple
        onChange={(event) => setFiles(Array.from(event.target.files || []))}
        type="file"
      />
      <button className="primary-button" onClick={handleUpload} type="button">
        Upload Selected Files
      </button>
      {!datasetProfile && artifactCount > 0 ? (
        <p className="muted-copy">Files uploaded. Run Ingest to summarize tables and notes into the project profile.</p>
      ) : null}
      {datasetProfile && ingestOutOfDate ? (
        <p className="muted-copy">Uploaded files changed since the last ingest. Run Ingest again to refresh the project profile.</p>
      ) : null}
      <div className="stats-grid">
        <div className="stat-card">
          <span>Artifacts</span>
          <strong>{artifactCount}</strong>
        </div>
        <div className="stat-card">
          <span>Tables</span>
          <strong>{tableCount}</strong>
        </div>
      </div>
      {visibleArtifacts.length ? (
        <div className="artifact-list">
          {visibleArtifacts.map((artifact) => (
            <div className="artifact-chip artifact-row" key={artifact.id}>
              <span>{artifact.filename}</span>
              <button
                aria-label={`Delete ${artifact.filename}`}
                className="ghost-button artifact-delete-button"
                disabled={deletingArtifactId === artifact.id}
                onClick={() => handleDeleteArtifact(artifact.id)}
                type="button"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
