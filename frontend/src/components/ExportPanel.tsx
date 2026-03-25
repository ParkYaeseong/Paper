import { stageIsBusy, stageRunLabel, stageRunningLabel } from "../lib/stages";
import type { ExportBundle, JobRun } from "../lib/types";


type ExportPanelProps = {
  exportBundle: ExportBundle;
  jobs: JobRun[];
  pendingStage: string | null;
  onRunStage: (stage: string) => Promise<void>;
};


export default function ExportPanel({ exportBundle, jobs, pendingStage, onRunStage }: ExportPanelProps) {
  const exportBusy = stageIsBusy("export", jobs, pendingStage);
  const failedJob = [...jobs].reverse().find((job) => job.status === "failed") ?? null;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Output</p>
          <h3>Export</h3>
        </div>
        <button className="primary-button" disabled={exportBusy} onClick={() => onRunStage("export")} type="button">
          {exportBusy ? stageRunningLabel("export") : stageRunLabel("export")}
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
        <p className="muted-copy">No export bundle yet. Run export after evidence review.</p>
      )}
      {failedJob?.log_text ? <p className="error-text">{failedJob.log_text}</p> : null}
    </section>
  );
}
