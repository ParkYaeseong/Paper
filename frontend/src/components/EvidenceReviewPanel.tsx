import { stageIsBusy, stageRunLabel, stageRunningLabel } from "../lib/stages";
import type { CitationSlot, EvidenceMatch, JobRun, ReferenceRecord } from "../lib/types";


type EvidenceReviewPanelProps = {
  citationSlots: CitationSlot[];
  evidenceMatches: EvidenceMatch[];
  jobs: JobRun[];
  pendingStage: string | null;
  references: ReferenceRecord[];
  onRunStage: (stage: string) => Promise<void>;
  onReviewSlot: (slotId: string, status: string, selectedReferenceIds?: string[]) => Promise<void>;
};


function scoreLabel(score: number) {
  if (score >= 0.2) return "Supported";
  if (score >= 0.08) return "Weak";
  return "Manual review";
}


export default function EvidenceReviewPanel({
  citationSlots,
  evidenceMatches,
  jobs,
  pendingStage,
  references,
  onRunStage,
  onReviewSlot
}: EvidenceReviewPanelProps) {
  const refById = Object.fromEntries(references.map((reference) => [reference.id, reference]));
  const matchBySlotId = Object.fromEntries(evidenceMatches.map((match) => [match.citation_slot_id, match]));
  const evidenceBusy = stageIsBusy("evidence", jobs, pendingStage);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Grounding</p>
          <h3>Evidence Review</h3>
        </div>
        <div className="button-row">
          <button className="secondary-button" disabled={evidenceBusy} onClick={() => onRunStage("evidence")} type="button">
            {evidenceBusy ? stageRunningLabel("evidence") : stageRunLabel("evidence")}
          </button>
        </div>
      </div>
      {citationSlots.length ? (
        <div className="evidence-list">
          {citationSlots.map((slot) => {
            const match = matchBySlotId[slot.id];
            const selectedRefs = (match?.selected_reference_ids_json || [])
              .map((referenceId) => refById[referenceId])
              .filter(Boolean);
            return (
              <article className="evidence-card" key={slot.id}>
                <div className="evidence-header">
                  <div>
                    <span>{slot.slot_key}</span>
                    <strong>{slot.claim_text}</strong>
                  </div>
                  <span className={`support-pill support-${slot.status}`}>{match ? scoreLabel(match.support_score) : slot.status}</span>
                </div>
                <p className="evidence-meta">{slot.context_text}</p>
                {selectedRefs.length ? (
                  <ul className="reference-list">
                    {selectedRefs.map((reference) => (
                      <li key={reference.id}>
                        <strong>{reference.title}</strong>
                        <span>{reference.venue || reference.source}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted-copy">No selected evidence yet.</p>
                )}
                <div className="button-row">
                  <button className="ghost-button" onClick={() => onReviewSlot(slot.id, "reviewed", match?.selected_reference_ids_json)} type="button">
                    Mark Reviewed
                  </button>
                  <button className="ghost-button" onClick={() => onReviewSlot(slot.id, "manual_review", match?.selected_reference_ids_json)} type="button">
                    Needs Review
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <p className="muted-copy">No citation slots yet. Planning creates the claims that need evidence.</p>
      )}
    </section>
  );
}
