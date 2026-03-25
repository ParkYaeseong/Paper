# Paper Quality, Run All, and Figure Generation Design

## Goal

Improve manuscript quality across all projects by replacing manual stage-heavy execution with a guided `Run All` workflow, adding a submission-grade quality gate, and generating figure candidates automatically through PaperBanana.

## Context

The current Paper workflow can generate a usable draft, but it still exposes too much pipeline detail to the user and allows low-quality exports too easily. The main failure modes are:

- irrelevant or weak references survive evidence grounding
- unresolved placeholders remain in the manuscript
- results sections stay generic and do not reflect actual uploaded artifacts
- figure placeholders are exported instead of being turned into real candidate figures
- users must manually step through too many internal pipeline stages

These issues are structural rather than cosmetic. They come from the lack of a quality audit layer, the lack of a guided orchestration path, and the absence of a figure generation integration.

## Approach Options

### Option 1: Tune retrieval and export warnings only

- Pros: smallest change set
- Cons: leaves generic draft quality, missing figures, and manual workflow complexity mostly untouched

### Option 2: Add a quality-oriented orchestration layer with automated figure generation

- Pros: addresses relevance, placeholders, results quality, export safety, and UX in one architecture
- Pros: keeps expert-level manual controls while making the default path much simpler
- Cons: requires new models, jobs, UI states, and PaperBanana integration

### Option 3: Split by manuscript type with separate end-to-end pipelines

- Pros: strongest long-term specialization
- Cons: too heavy for the current product stage and overfits before the common quality layer exists

## Recommendation

Use **Option 2**.

Add a backend orchestration stage named `run_all` that executes the normal pipeline in sequence and stops in a review-ready state before export. Add a new `quality` stage that audits citations, placeholders, section completeness, and positioning. Add a new `figures` stage that turns figure placeholders into PaperBanana figure specs and generated candidate assets. Finally, split export into `Draft Export` and `Final Export`, with only the latter blocked by critical quality issues.

## Workflow

### Default user flow

1. Upload project files
2. Click `Run All`
3. Wait while the system runs:
   - `ingest`
   - `plan`
   - `draft`
   - `evidence`
   - `quality`
   - `figures`
4. Review quality findings and figure candidates
5. Export:
   - `Draft Export` for working drafts
   - `Final Export` only when critical issues are cleared

### Advanced flow

Advanced users can still open an `Advanced` panel and rerun individual stages such as `evidence`, `quality`, or `figures` without re-running the full pipeline.

## Quality Model

Add a persistent `QualityReport` for each project version. It contains:

- `critical_issues_json`
- `warnings_json`
- `recommended_actions_json`
- `submission_ready`

### Critical issues

Critical issues block `Final Export`.

Examples:

- unresolved citation tokens remain in rendered content
- `[manual review]` remains in the manuscript
- a citation slot has no selected supporting reference
- figure placeholders remain unresolved
- core sections are missing

### Warnings

Warnings do not block `Final Export` by themselves, but they are shown prominently.

Examples:

- weakly supported citations
- overly generic results language
- weak related work positioning
- limitations or practical utility sections are shallow

## Figure Generation Model

Figure generation should not overwrite the manuscript directly. Use a structured flow:

1. `draft` creates figure placeholders
2. `quality` identifies unresolved figure requirements
3. `figures` creates `FigureSpec` records
4. `figures` calls PaperBanana to generate one or more candidate images per spec
5. generated outputs are stored as `Artifact(kind=figure_candidate)`
6. the user chooses the preferred candidate in review
7. export embeds the selected figure or blocks `Final Export` if none is selected where required

Each `FigureSpec` stores:

- `figure_key`
- `figure_number`
- `section_key`
- `caption_draft`
- `source_excerpt`
- `visual_intent`
- `status`

Each generated result is stored as `FigureAsset` linked to both the spec and the stored artifact.

## PaperBanana Integration

Do not import PaperBanana modules directly into Paper.

Use PaperBanana as an adjacent runtime dependency that Paper calls through a controlled adapter. The adapter should:

- prepare a text input from the section excerpt and figure caption draft
- invoke PaperBanana in a predictable local execution mode
- collect generated image files and metadata
- normalize them into `FigureAsset` rows and stored artifact paths

This keeps Paper and PaperBanana loosely coupled and lets each service evolve independently.

## API and Job Changes

### New pipeline stages

- `quality`
- `figures`
- `run_all`

### Orchestration rules

- `run_all` enqueues or executes stages sequentially in one orchestrated job
- it stops immediately on the first failed stage
- it does not auto-export
- it records which stage failed and why

### Export rules

- `Draft Export` is always allowed
- `Final Export` is allowed only when the latest `QualityReport.submission_ready` is true

## UI Changes

### Main controls

- Add `Run All` as the primary call to action
- Replace the current stage-by-stage emphasis with a simpler default flow
- Keep individual stage buttons inside an `Advanced` panel

### Review panels

- `Quality Summary`
  - critical issue count
  - warning count
  - recommended actions
  - final-export readiness
- `Figure Review`
  - figure specs
  - candidate thumbnails
  - selected candidate state
  - regenerate action

### Export panel

- show both `Draft Export` and `Final Export`
- explain why `Final Export` is blocked when critical issues remain

## Testing

### Backend

- quality report generation for placeholder and citation failures
- submission-ready true/false behavior
- run_all orchestration ordering and stop-on-failure behavior
- figure spec generation from placeholders
- PaperBanana adapter with mocked process output
- final export blocked when critical issues exist

### Frontend

- `Run All` visibility and loading state
- `Advanced` toggle and manual stage rerun
- quality summary rendering
- final export disabled when blocked
- figure review selection flow

### Integration

- upload -> run_all -> review-ready state
- failed quality or figure stage leaves the project in a diagnosable state
- selected figure assets appear in export manifests

