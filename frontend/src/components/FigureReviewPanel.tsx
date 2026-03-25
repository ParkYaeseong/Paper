import type { FigureSpec } from "../lib/types";
import { stageIsBusy, stageRunLabel, stageRunningLabel } from "../lib/stages";
import type { JobRun } from "../lib/types";


type FigureReviewPanelProps = {
  figureSpecs: FigureSpec[];
  onRunStage: () => Promise<void>;
  showManualControls: boolean;
  jobs?: JobRun[];
  pendingStage?: string | null;
};


async function copyText(text: string) {
  if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  if (typeof document === "undefined") {
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "absolute";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  if (typeof document.execCommand === "function") {
    document.execCommand("copy");
  }
  document.body.removeChild(textarea);
}


export default function FigureReviewPanel({
  figureSpecs,
  onRunStage,
  showManualControls,
  jobs = [],
  pendingStage = null,
}: FigureReviewPanelProps) {
  const figuresBusy = stageIsBusy("figures", jobs, pendingStage);
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Figures</p>
          <h3>Figure Review</h3>
        </div>
        {showManualControls ? (
          <button className="secondary-button" disabled={figuresBusy} onClick={() => void onRunStage()} type="button">
            {figuresBusy ? stageRunningLabel("figures") : stageRunLabel("figures")}
          </button>
        ) : null}
      </div>
      {figureSpecs.length ? (
        <div className="figure-spec-list">
          {figureSpecs.map((spec) => (
            <article className="figure-spec-card" key={spec.id}>
              <div className="figure-spec-header">
                <div>
                  <span>{`Figure ${spec.figure_number}`}</span>
                  <strong>{spec.caption_draft}</strong>
                </div>
                <span className="status-pill">{spec.status}</span>
              </div>
              <p className="evidence-meta">{spec.section_key}</p>
              <p className="muted-copy">
                Paste the method content and caption into PaperBanana. Choose aspect ratio, candidate count, and refinement settings there.
              </p>
              <div className="figure-spec-list">
                <div className="figure-spec-card">
                  <div className="figure-spec-header">
                    <strong>Method Section Content</strong>
                    <button
                      className="ghost-button"
                      onClick={() => void copyText(spec.method_section_content)}
                      type="button"
                    >
                      Copy method content
                    </button>
                  </div>
                  <pre className="muted-copy">{spec.method_section_content}</pre>
                </div>
                <div className="figure-spec-card">
                  <div className="figure-spec-header">
                    <strong>Figure Caption</strong>
                    <button className="ghost-button" onClick={() => void copyText(spec.caption_draft)} type="button">
                      Copy figure caption
                    </button>
                  </div>
                  <pre className="muted-copy">{spec.caption_draft}</pre>
                </div>
              </div>
              <div className="quality-list">
                <h4>Source context</h4>
                <p className="muted-copy">{spec.source_excerpt}</p>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">No figure handoff text yet. Run All or the figure stage to prepare PaperBanana-ready caption and method content.</p>
      )}
    </section>
  );
}
