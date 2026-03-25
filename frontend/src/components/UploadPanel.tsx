import { useRef, useState } from "react";

import { ARTIFACT_ROLE_OPTIONS, artifactRoleLabel, defaultArtifactRoleForFilename, type ArtifactRole } from "../lib/artifactRoles";
import { stageIsBusy, stageRunLabel, stageRunningLabel } from "../lib/stages";
import type { Artifact, DatasetProfile, JobRun, Project } from "../lib/types";


type PendingUpload = {
  file: File;
  role: ArtifactRole;
};

type UploadPanelProps = {
  artifacts: Artifact[];
  project: Project;
  datasetProfile: DatasetProfile;
  jobs: JobRun[];
  pendingStage: string | null;
  showManualControls: boolean;
  onDeleteArtifact: (artifactId: string) => Promise<void>;
  onUpdateArtifactRole: (artifactId: string, role: ArtifactRole) => Promise<void>;
  onUploadFiles: (uploads: PendingUpload[]) => Promise<void>;
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
  onUpdateArtifactRole,
  onUploadFiles,
  onRunStage,
}: UploadPanelProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploads, setUploads] = useState<PendingUpload[]>([]);
  const [deletingArtifactId, setDeletingArtifactId] = useState<string | null>(null);
  const [updatingArtifactId, setUpdatingArtifactId] = useState<string | null>(null);
  const summary = datasetProfile?.summary_json?.dataset_summary as
    | {
      artifact_count?: number;
      table_count?: number;
      source_artifacts?: Array<{
        artifact_id?: string;
        sha256?: string;
        role?: string;
      }>;
    }
    | undefined;
  const artifactCount = artifacts.length;
  const inferredTableCount = artifacts.filter((artifact) => artifact.role === "results_table").length;
  const currentSourceSignature = artifacts
    .map((artifact) => `${artifact.id}:${artifact.sha256}:${artifact.role}`)
    .sort();
  const ingestedSourceSignature = (summary?.source_artifacts || [])
    .map((artifact) => `${artifact.artifact_id || ""}:${artifact.sha256 || ""}:${artifact.role || ""}`)
    .sort();
  const ingestOutOfDate = Boolean(
    datasetProfile
      && (
        summary?.artifact_count !== artifactCount
        || summary?.table_count !== inferredTableCount
        || currentSourceSignature.join("|") !== ingestedSourceSignature.join("|")
      ),
  );
  const tableCount = ingestOutOfDate ? inferredTableCount : (summary?.table_count ?? inferredTableCount);
  const visibleArtifacts = artifacts;
  const ingestBusy = stageIsBusy("ingest", jobs, pendingStage);

  async function handleUpload() {
    if (!uploads.length) return;
    await onUploadFiles(uploads);
    setUploads([]);
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

  async function handleRoleUpdate(artifactId: string, role: ArtifactRole) {
    setUpdatingArtifactId(artifactId);
    try {
      await onUpdateArtifactRole(artifactId, role);
    } finally {
      setUpdatingArtifactId(null);
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
        aria-label="Choose upload files"
        ref={fileInputRef}
        multiple
        onChange={(event) => setUploads(
          Array.from(event.target.files || []).map((file) => ({
            file,
            role: defaultArtifactRoleForFilename(file.name),
          })),
        )}
        type="file"
      />
      {uploads.length ? (
        <div className="artifact-list pending-upload-list">
          {uploads.map((upload, index) => (
            <div className="artifact-chip artifact-row artifact-role-row" key={`${upload.file.name}-${index}`}>
              <div className="artifact-main">
                <strong>{upload.file.name}</strong>
                <span className="status-pill">{artifactRoleLabel(upload.role)}</span>
              </div>
              <label className="artifact-role-field">
                <span className="sr-only">Role for {upload.file.name}</span>
                <select
                  aria-label={`Role for ${upload.file.name}`}
                  onChange={(event) => {
                    const nextRole = event.target.value as ArtifactRole;
                    setUploads((current) => current.map((item, itemIndex) => (
                      itemIndex === index ? { ...item, role: nextRole } : item
                    )));
                  }}
                  value={upload.role}
                >
                  {ARTIFACT_ROLE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ))}
        </div>
      ) : null}
      <button className="primary-button" disabled={!uploads.length} onClick={handleUpload} type="button">
        Upload Selected Files
      </button>
      {!datasetProfile && artifactCount > 0 ? (
        <p className="muted-copy">Files uploaded. Run Ingest to summarize tables and notes into the project profile.</p>
      ) : null}
      {datasetProfile && ingestOutOfDate ? (
        <p className="muted-copy">Uploaded files or roles changed since the last ingest. Run Ingest again to refresh the project profile.</p>
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
            <div className="artifact-chip artifact-row artifact-role-row" key={artifact.id}>
              <div className="artifact-main">
                <strong>{artifact.filename}</strong>
                <span className="status-pill">{artifactRoleLabel(artifact.role)}</span>
              </div>
              <div className="artifact-actions">
                <label className="artifact-role-field">
                  <span className="sr-only">Uploaded role for {artifact.filename}</span>
                  <select
                    aria-label={`Uploaded role for ${artifact.filename}`}
                    disabled={updatingArtifactId === artifact.id}
                    onChange={(event) => void handleRoleUpdate(artifact.id, event.target.value as ArtifactRole)}
                    value={artifact.role}
                  >
                    {ARTIFACT_ROLE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
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
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
