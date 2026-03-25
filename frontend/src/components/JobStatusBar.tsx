import type { JobNotice } from "../lib/stages";
import { parseRunAllSubstage, stageDescription, stageLabel, stageStatusTitle } from "../lib/stages";


type JobStatusBarProps = {
  notice: JobNotice;
};


export default function JobStatusBar({ notice }: JobStatusBarProps) {
  const tone = notice.status === "failed" ? "danger" : notice.status === "succeeded" ? "success" : "active";
  const runAllSubstage = notice.stage === "run_all" && notice.status === "running" ? parseRunAllSubstage(notice.logText) : null;
  const title = runAllSubstage ? `Running ${stageLabel(runAllSubstage)}` : stageStatusTitle(notice.stage, notice.status);
  const copy =
    notice.status === "failed" && notice.logText
      ? notice.logText
      : runAllSubstage
        ? stageDescription(runAllSubstage)
        : stageDescription(notice.stage);

  return (
    <aside aria-live="polite" className={`job-status-bar ${tone}`} role="status">
      <span className="job-status-eyebrow">Pipeline status</span>
      <strong>{title}</strong>
      <p>{copy}</p>
    </aside>
  );
}
