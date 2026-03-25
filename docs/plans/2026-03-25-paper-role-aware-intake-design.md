# Paper Role-Aware Intake and Full-Text Ingestion Design

## Goal

Replace the current preview-only upload handling with a role-aware intake pipeline that lets users label uploaded files explicitly, reads narrative files as full text, and processes results tables separately from prose so manuscript planning and drafting use the right evidence.

## Context

The current upload path is good enough for a demo, but it is structurally wrong for serious manuscript generation:

- `.md` and `.txt` files are truncated to a short preview during ingest
- planning and drafting read one blended summary instead of distinct context layers
- repository READMEs and paper-intake briefs are treated with the same weight
- results tables are counted but not treated as a separate results-focused input class

This produces generic outlines, weak section focus, and poor system-paper positioning. It also makes mixed uploads fragile: a strong `project_intake_system_paper.md` can be diluted by a large README or operational document.

## Approach Options

### Option 1: Increase preview size and keep the current blended profile

- Pros: smallest change
- Cons: does not solve the root problem that narrative, supporting docs, and results are mixed together

### Option 2: Add explicit upload roles and role-aware ingest

- Pros: lets the user state intent directly
- Pros: separates narrative framing from results evidence
- Pros: fixes current quality failures without inventing a complex classifier
- Cons: requires API, UI, and ingest changes together

### Option 3: Split the upload UI into multiple dedicated dropzones

- Pros: very explicit
- Cons: heavier UI redesign and more cumbersome artifact editing

## Recommendation

Use **Option 2**.

Keep one upload surface, but require each uploaded file to have a user-selected role. Persist that role on the artifact, allow changing it later, and make ingest/planning/drafting treat each role differently.

## File Roles

Use four initial roles:

- `narrative_brief`
  - paper framing, project intake, manuscript direction
- `supporting_doc`
  - README, usage docs, architecture notes, implementation notes
- `results_table`
  - CSV or structured experimental/result data
- `background_reference`
  - lower-priority notes, older drafts, background material

These roles should be stored on each artifact, exposed in the API, shown in the UI, and editable after upload.

## Ingestion Model

### Narrative and supporting files

Do not store a short preview as the primary input.

Instead:

1. read the full text
2. normalize whitespace
3. split first by headings when possible
4. chunk large sections into manageable segments
5. persist chunk records so later stages can use relevant pieces rather than the whole file blob

`narrative_brief` chunks become the highest-priority manuscript context.

`supporting_doc` chunks are lower priority and mainly used to reinforce system details, architecture, and workflow descriptions.

`background_reference` chunks are lowest priority and should not override the main narrative.

### Results tables and experimental values

Yes: tables and experiment values should go through a separate path.

`results_table` artifacts should not be handled like prose. They should produce structured result summaries such as:

- row and column counts
- numeric vs categorical columns
- grouped statistics or key ranges where possible
- representative rows
- candidate result statements for methods/results sections

The manuscript pipeline should then consume these summaries as `results_context`, distinct from narrative context.

## Persisted Context Structure

`DatasetProfile.summary_json` should evolve from one blended object into layered context:

- `project_brief`
- `narrative_context`
- `supporting_context`
- `results_context`
- `background_context`

In addition, add a persistent artifact-chunk table so later stages can reference exact chunks instead of only derived summaries.

## Planning Changes

Planning should consume:

- project title
- objective
- top `narrative_brief` chunks
- condensed `supporting_doc` chunks
- structured `results_context`

Planning should also use manuscript-type heuristics. In particular, system/platform papers should favor sections such as:

- Problem / Motivation
- System Overview
- Architecture
- Workflow
- Evaluation or Use Cases
- Discussion / Limitations

This is especially important for repositories like `protein_pipeline`, where the publishable contribution is workflow orchestration and interactive analysis rather than a single new model.

## Drafting Changes

Drafting should become section-aware in its source selection:

- `Introduction`
  - objective + narrative brief + supporting docs
- `Methods` / `System Overview`
  - supporting docs + architecture/workflow chunks
- `Results` / `Evaluation`
  - structured results context first
  - if no results exist, explicitly fall back to system capabilities or usage scenarios and let quality audit warn about weak results
- `Discussion`
  - narrative + results + grounded evidence

This avoids the current failure mode where the whole manuscript is generated from the same diluted context payload.

## API and UI Changes

### Upload flow

- Each selected file gets a role dropdown before upload.
- Upload submits `files[]` plus matching role metadata.
- Artifact rows return their current role to the frontend.

### Artifact management

- Uploaded artifact list shows a role badge or role select.
- Users can change a role after upload.
- Changing a role marks ingest as stale.

### Ingest guidance

- If uploads change or roles change, the UI should tell the user that `Run Ingest` or `Run All` must be rerun to rebuild manuscript context.

## Quality Impact

This change is expected to improve manuscript quality in several direct ways:

- paper-intake briefs keep control over manuscript framing
- repository READMEs become supporting material rather than dominant context
- results tables influence methods/results sections directly
- generic system-paper drafts are less likely because distinctive contribution bullets can be extracted from narrative chunks

## Testing

### Backend

- upload persists artifact roles
- artifact roles can be edited
- narrative files are chunked as full text instead of preview-only
- results tables produce separate structured summaries
- planning receives role-aware context
- drafting uses section-specific context selection

### Frontend

- role selection before upload
- role display and editing after upload
- stale-ingest messaging when roles change

### Integration

- `project_intake_system_paper.md` alone drives strong planning
- `project_intake_system_paper.md + README` still prioritizes `narrative_brief`
- results tables affect results-oriented context instead of being treated like notes
