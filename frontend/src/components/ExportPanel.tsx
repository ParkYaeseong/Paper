import type { ExportBundle, JobRun } from "../lib/types";


type ExportPanelProps = {
  exportBundle: ExportBundle;
  jobs: JobRun[];
  onRunStage: (stage: string) => Promise<void>;
};


export default function ExportPanel({ exportBundle, jobs, onRunStage }: ExportPanelProps) {
  const exportBusy = jobs.some((job) => job.stage === "export" && (job.status === "queued" || job.status === "running"));
  const failedJob = [...jobs].reverse().find((job) => job.status === "failed") ?? null;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Output</p>
          <h3>Export</h3>
        </div>
        <button className="primary-button" disabled={exportBusy} onClick={() => onRunStage("export")} type="button">
          Run Export
        </button>
      </div>
      {exportBundle ? (
        <div className="export-grid">
          {Object.entries(exportBundle.download_urls).map(([label, href]) => (
            <a className="export-link" href={href} key={label}>
              <span>{label.toUpperCase()}</span>
              <strong>Download</strong>
            </a>
          ))}
        </div>
      ) : (
        <p className="muted-copy">No export bundle yet. Run export after grounding and review.</p>
      )}
      {failedJob?.log_text ? <p className="error-text">{failedJob.log_text}</p> : null}
      <div className="job-strip">
        {jobs.slice(-6).map((job) => (
          <div className="job-chip" key={job.id}>
            <span>{job.stage}</span>
            <strong>{job.status}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
