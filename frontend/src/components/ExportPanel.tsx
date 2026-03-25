import { stageIsBusy, stageRunningLabel } from "../lib/stages";
import type { ExportBundle, JobRun, QualityReport } from "../lib/types";


type ExportPanelProps = {
  exportBundle: ExportBundle;
  jobs: JobRun[];
  pendingStage: string | null;
  qualityReport: QualityReport;
  onRunExport: (mode: "draft" | "final") => Promise<void>;
};


export default function ExportPanel({ exportBundle, jobs, pendingStage, qualityReport, onRunExport }: ExportPanelProps) {
  const exportBusy = stageIsBusy("export", jobs, pendingStage);
  const failedJob = [...jobs].reverse().find((job) => job.status === "failed") ?? null;
  const finalBlocked = !qualityReport?.submission_ready;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Output</p>
          <h3>Export</h3>
        </div>
        <div className="button-row">
          <button className="secondary-button" disabled={exportBusy} onClick={() => onRunExport("draft")} type="button">
            {exportBusy ? stageRunningLabel("export") : "Draft Export"}
          </button>
          <button className="primary-button" disabled={exportBusy || finalBlocked} onClick={() => onRunExport("final")} type="button">
            {exportBusy ? stageRunningLabel("export") : "Final Export"}
          </button>
        </div>
      </div>
      {finalBlocked ? (
        <p className="muted-copy">Final Export unlocks after all critical quality issues are cleared.</p>
      ) : (
        <p className="muted-copy">Final Export is available because the latest quality report has no critical issues.</p>
      )}
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
        <p className="muted-copy">No export bundle yet. Run Draft Export for a working manuscript or Final Export for a gated submission-ready bundle.</p>
      )}
      {failedJob?.log_text ? <p className="error-text">{failedJob.log_text}</p> : null}
    </section>
  );
}
