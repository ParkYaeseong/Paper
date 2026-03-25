import { stageIsBusy, stageRunLabel, stageRunningLabel } from "../lib/stages";
import type { JobRun, QualityReport } from "../lib/types";


type QualitySummaryPanelProps = {
  qualityReport: QualityReport;
  jobs?: JobRun[];
  pendingStage?: string | null;
  showManualControls?: boolean;
  onRunStage?: (stage: string) => Promise<void>;
};


function pluralize(count: number, singular: string, plural: string) {
  return `${count} ${count === 1 ? singular : plural}`;
}


export default function QualitySummaryPanel({
  qualityReport,
  jobs = [],
  pendingStage = null,
  showManualControls = false,
  onRunStage,
}: QualitySummaryPanelProps) {
  const criticalCount = qualityReport?.critical_issues_json.length ?? 0;
  const warningCount = qualityReport?.warnings_json.length ?? 0;
  const qualityBusy = stageIsBusy("quality", jobs, pendingStage);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Quality Gate</p>
          <h3>Quality Summary</h3>
        </div>
        <div className="button-row">
          <span className={`status-pill ${qualityReport?.submission_ready ? "status-ready" : "status-blocked"}`}>
            {qualityReport?.submission_ready ? "Final export ready" : "Final export blocked"}
          </span>
          {showManualControls && onRunStage ? (
            <button className="secondary-button" disabled={qualityBusy} onClick={() => void onRunStage("quality")} type="button">
              {qualityBusy ? stageRunningLabel("quality") : stageRunLabel("quality")}
            </button>
          ) : null}
        </div>
      </div>
      {qualityReport ? (
        <div className="quality-summary">
          <div className="stats-grid">
            <div className="stat-card">
              <span>Critical</span>
              <strong>{criticalCount}</strong>
              <p>{pluralize(criticalCount, "critical issue", "critical issues")}</p>
            </div>
            <div className="stat-card">
              <span>Warnings</span>
              <strong>{warningCount}</strong>
              <p>{pluralize(warningCount, "warning", "warnings")}</p>
            </div>
          </div>
          {qualityReport.critical_issues_json.length ? (
            <div className="quality-list">
              <h4>Critical issues</h4>
              <ul className="issue-list">
                {qualityReport.critical_issues_json.map((issue) => (
                  <li key={`${issue.code}-${issue.message}`}>{issue.message}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {qualityReport.warnings_json.length ? (
            <div className="quality-list">
              <h4>Warnings</h4>
              <ul className="issue-list">
                {qualityReport.warnings_json.map((issue) => (
                  <li key={`${issue.code}-${issue.message}`}>{issue.message}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {qualityReport.recommended_actions_json.length ? (
            <div className="quality-list">
              <h4>Recommended actions</h4>
              <ul className="issue-list">
                {qualityReport.recommended_actions_json.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : (
        <p className="muted-copy">Run All or the quality stage to generate a submission-readiness report.</p>
      )}
    </section>
  );
}
