import { useState } from "react";

import type { DatasetProfile, Project } from "../lib/types";


type UploadPanelProps = {
  project: Project;
  datasetProfile: DatasetProfile;
  onUploadFiles: (files: File[]) => Promise<void>;
  onRunStage: (stage: string) => Promise<void>;
};


export default function UploadPanel({ project, datasetProfile, onUploadFiles, onRunStage }: UploadPanelProps) {
  const [files, setFiles] = useState<File[]>([]);
  const summary = datasetProfile?.summary_json?.dataset_summary as
    | { artifact_count?: number; table_count?: number }
    | undefined;

  async function handleUpload() {
    if (!files.length) return;
    await onUploadFiles(files);
    setFiles([]);
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Project Intake</p>
          <h3>Upload</h3>
        </div>
        <button className="secondary-button" onClick={() => onRunStage("ingest")} type="button">
          Run Ingest
        </button>
      </div>
      <p className="panel-copy">{project.objective || "Add an objective to anchor the planning stage."}</p>
      <input
        multiple
        onChange={(event) => setFiles(Array.from(event.target.files || []))}
        type="file"
      />
      <button className="primary-button" onClick={handleUpload} type="button">
        Upload Selected Files
      </button>
      <div className="stats-grid">
        <div className="stat-card">
          <span>Artifacts</span>
          <strong>{summary?.artifact_count ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span>Tables</span>
          <strong>{summary?.table_count ?? 0}</strong>
        </div>
      </div>
    </section>
  );
}
