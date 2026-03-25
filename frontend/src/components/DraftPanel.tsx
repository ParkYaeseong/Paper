import { useState } from "react";

import { stageIsBusy, stageRunLabel, stageRunningLabel } from "../lib/stages";
import type { DraftSection, JobRun } from "../lib/types";


type DraftPanelProps = {
  draftSections: DraftSection[];
  jobs: JobRun[];
  pendingStage: string | null;
  showManualControls: boolean;
  onRunStage: (stage: string) => Promise<void>;
  onSaveSection: (sectionId: string, content: string) => Promise<void>;
};


export default function DraftPanel({
  draftSections,
  jobs,
  pendingStage,
  showManualControls,
  onRunStage,
  onSaveSection
}: DraftPanelProps) {
  const [localEdits, setLocalEdits] = useState<Record<string, string>>({});
  const draftBusy = stageIsBusy("draft", jobs, pendingStage);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Drafting</p>
          <h3>Workspace</h3>
        </div>
        {showManualControls ? (
          <button className="secondary-button" disabled={draftBusy} onClick={() => onRunStage("draft")} type="button">
            {draftBusy ? stageRunningLabel("draft") : stageRunLabel("draft")}
          </button>
        ) : null}
      </div>
      {draftSections.length ? (
        <div className="draft-grid">
          {draftSections.map((section) => (
            <article className="draft-card" key={section.id}>
              <div className="draft-card-header">
                <div>
                  <span>{section.section_key}</span>
                  <strong>{section.heading}</strong>
                </div>
                <span className="status-pill">{section.status}</span>
              </div>
              <textarea
                className="draft-editor"
                onChange={(event) =>
                  setLocalEdits((current) => ({ ...current, [section.id]: event.target.value }))
                }
                value={localEdits[section.id] ?? section.content}
              />
              <button
                className="ghost-button"
                onClick={() => onSaveSection(section.id, localEdits[section.id] ?? section.content)}
                type="button"
              >
                Save Section
              </button>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">No draft sections yet. Run the draft stage after planning.</p>
      )}
    </section>
  );
}
