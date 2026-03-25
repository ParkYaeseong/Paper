import type { FigureSpec } from "../lib/types";
import { stageIsBusy, stageRunLabel, stageRunningLabel } from "../lib/stages";
import type { JobRun } from "../lib/types";


type FigureReviewPanelProps = {
  figureSpecs: FigureSpec[];
  onRunStage: () => Promise<void>;
  onSelectFigureAsset: (figureSpecId: string, figureAssetId: string) => Promise<void>;
  showManualControls: boolean;
  jobs?: JobRun[];
  pendingStage?: string | null;
};


export default function FigureReviewPanel({
  figureSpecs,
  onRunStage,
  onSelectFigureAsset,
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
              <p className="muted-copy">{spec.source_excerpt}</p>
              <div className="figure-candidate-grid">
                {spec.assets.map((asset) => (
                  <div className={`figure-candidate-card ${asset.selected ? "selected" : ""}`} key={asset.id}>
                    <img alt={asset.filename} className="figure-preview" src={asset.download_url} />
                    <div className="figure-candidate-meta">
                      <strong>{asset.filename}</strong>
                      {asset.selected ? (
                        <span className="status-pill status-ready">Selected</span>
                      ) : (
                        <button className="ghost-button" onClick={() => void onSelectFigureAsset(spec.id, asset.id)} type="button">
                          {`Select ${asset.filename}`}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">No figure candidates yet. Run All or the figure stage to generate candidate visuals.</p>
      )}
    </section>
  );
}
