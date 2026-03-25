import type { JobRun, Outline } from "../lib/types";


type OutlinePanelProps = {
  outline: Outline;
  jobs: JobRun[];
  onRunStage: (stage: string) => Promise<void>;
};


export default function OutlinePanel({ outline, jobs, onRunStage }: OutlinePanelProps) {
  const planBusy = jobs.some((job) => job.stage === "plan" && (job.status === "queued" || job.status === "running"));
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Planning</p>
          <h3>Outline</h3>
        </div>
        <button className="secondary-button" disabled={planBusy} onClick={() => onRunStage("plan")} type="button">
          Run Plan
        </button>
      </div>
      {outline ? (
        <div className="outline-list">
          <div className="outline-card accent">
            <span>Manuscript type</span>
            <strong>{outline.manuscript_type}</strong>
          </div>
          {outline.title_candidates_json.map((title) => (
            <div className="outline-card" key={title}>
              <span>Title candidate</span>
              <strong>{title}</strong>
            </div>
          ))}
          {(outline.outline_json.sections || []).map((section) => (
            <div className="outline-card" key={section.key}>
              <span>{section.key}</span>
              <strong>{section.heading}</strong>
              <p>{(section.claims || []).length} citation-aware claim(s)</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted-copy">No outline yet. Run the planning stage after ingest.</p>
      )}
    </section>
  );
}
