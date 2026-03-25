import type { JobNotice } from "../lib/stages";
import { stageDescription, stageStatusTitle } from "../lib/stages";


type JobStatusBarProps = {
  notice: JobNotice;
};


export default function JobStatusBar({ notice }: JobStatusBarProps) {
  const tone = notice.status === "failed" ? "danger" : notice.status === "succeeded" ? "success" : "active";
  const copy = notice.status === "failed" && notice.logText ? notice.logText : stageDescription(notice.stage);

  return (
    <aside aria-live="polite" className={`job-status-bar ${tone}`} role="status">
      <span className="job-status-eyebrow">Pipeline status</span>
      <strong>{stageStatusTitle(notice.stage, notice.status)}</strong>
      <p>{copy}</p>
    </aside>
  );
}
