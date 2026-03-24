# Paper Authoring System Design

## Goal

Build a KBF SSO-protected independent web application at `paper.k-biofoundrycopilot.duckdns.org` that turns uploaded internal research data into a manuscript draft, retrieves supporting literature, grounds claims with evidence, supports human review, and exports submission-oriented outputs.

## Deployment Boundary

- App root: `/opt/Paper`
- Public URL: `https://paper.k-biofoundrycopilot.duckdns.org`
- Identity provider: KBF Keycloak in `/opt/kbf-infra`
- Auth protocol: OIDC authorization code flow against the `kbf` realm
- App role model:
  - `paper-user`
  - `paper-admin`

The app will be deployed as an independent service, not as a feature inside `/opt/open-notebook`.

## System Architecture

```text
Caddy (kbf-infra)
  -> paper frontend
  -> paper API
       -> Postgres
       -> Redis
       -> worker
       -> local artifact storage
       -> vector index cache
```

The user sees a single web application. Internally, the backend separates manuscript generation into distinct pipeline stages so each stage can be retried, observed, and reviewed independently.

## Core Pipeline

1. Upload project artifacts
   - CSV, XLSX, PDF, DOCX, Markdown, figures, notes
2. Normalize project context
   - extract project metadata
   - summarize variables/findings/limitations
   - build a canonical dataset profile JSON
3. Plan manuscript
   - infer manuscript type
   - produce title candidates and section outline
   - insert citation placeholders by claim slot
4. Draft manuscript
   - generate section drafts with placeholders such as `[CIT_INTRO_1]`
5. Retrieve literature
   - search PubMed and OpenAlex
   - normalize DOI/metadata with Crossref when useful
6. Ground evidence
   - match claim slots to literature candidates
   - score support strength
   - mark unsupported or weak claims
7. Human review
   - inspect sentence-level support
   - edit text and reference selection
   - mark claims reviewed
8. Export outputs
   - canonical JSON
   - Markdown
   - BibTeX
   - DOCX
   - LaTeX best effort

## Model Strategy

- Primary planner/writer: `GPT-5.4`
  - outline generation
  - section drafting
  - structured manuscript planning output
- Secondary reviewer/long-context model: `Gemini 2.5 Pro`
  - cross-section consistency review
  - unsupported-claim detection
  - overstatement detection

Generation and retrieval remain separate. Citation insertion happens only after retrieval and grounding.

## Data Model

The top-level unit is `Project`.

### Main entities

- `User`
- `Project`
- `Artifact`
- `DatasetProfile`
- `Outline`
- `DraftSection`
- `CitationSlot`
- `ReferenceRecord`
- `EvidenceMatch`
- `ReviewDecision`
- `ExportBundle`
- `JobRun`

### Key modeling decisions

- All uploads are stored as `Artifact` records plus files on disk.
- Normalized research context is frozen as `DatasetProfile`.
- Draft text is stored by section and version, not as one mutable blob.
- Citation management is claim-slot-first, not reference-first.
- Final references are derived from selected evidence matches.

## Claim and Citation Model

Every generated claim that needs support gets a stable placeholder such as:

- `[CIT_INTRO_1]`
- `[CIT_DISCUSSION_3]`

Each placeholder maps to one `CitationSlot`. Grounding attaches an `EvidenceMatch` with:

- `claim_text`
- `queries`
- `candidate_papers`
- `selected_papers`
- `support_score`
- `status`

`status` values:

- `supported`
- `weak`
- `unsupported`
- `manual_review`
- `reviewed`

This makes the review UI sentence-centric instead of bibliography-centric.

## Retrieval and Grounding

### Retrieval sources

- PubMed
- OpenAlex
- Crossref for metadata normalization

### Retrieval flow

1. Extract claims from citation slots.
2. Generate 2-3 search queries per claim.
3. Retrieve candidate papers from PubMed and OpenAlex.
4. Merge and deduplicate records by DOI/title.
5. Rank candidates with lexical plus embedding signals.
6. Pass top candidates to the grounding stage.

### Grounding flow

1. Compare each claim against abstract and metadata evidence.
2. Compute a support score.
3. Select the best supporting papers when confidence is high enough.
4. Refuse insertion when support is weak.
5. Mark the claim for manual review when needed.

Grounding is hybrid:

- rules for candidate filtering and deduplication
- model-assisted reranking and support reasoning

## Human Review UI

The review experience centers on the manuscript itself.

### Required views

- project list
- project workspace
- outline editor
- section draft editor
- evidence review panel
- reference manager
- export panel

### Review signals

- `Supported`
- `Weak`
- `Unsupported`
- `Manual review`
- `Reviewed`

### Reviewer actions

- accept or reject evidence
- edit section text
- regenerate one section
- regenerate one grounding pass
- swap references
- mark claims reviewed

## Export Strategy

Canonical persisted outputs:

- `manuscript.json`
- `manuscript.md`
- `references.bib`

Derived outputs:

- `manuscript.docx`
- `manuscript.tex`

DOCX is the primary v1 output because it is the most practical format for collaborative review and near-submission editing.

## Storage

- System of record: Postgres
- Queue/cache: Redis
- File storage: local directories under `/opt/Paper/data`
- Literature cache and vector index: local directory under `/opt/Paper/data/vectorstore`

## Job Model

Long-running stages are represented as `JobRun` rows.

### Stages

- `ingest`
- `plan`
- `draft`
- `retrieve`
- `ground`
- `export`

### States

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`

This enables polling, retries, auditability, and per-stage reruns.

## Security and Access

- OIDC with Keycloak `kbf` realm
- session cookie on the paper app domain
- every project owned by an authenticated user
- admin role for operational visibility and intervention
- per-project authorization on uploads, drafts, evidence, and exports

## Recommended Stack

- Backend: FastAPI
- Frontend: React + Vite + TypeScript
- DB: Postgres
- Queue: Redis
- Workers: Python worker process
- LLM APIs: OpenAI, Gemini
- Literature APIs: PubMed, OpenAlex, Crossref
- Export libraries: Pandoc or python-docx for DOCX, bibtex tooling for references

## Testing Strategy

- backend unit tests for models, auth, planning, retrieval, grounding, export
- API tests for project workflow and authorization boundaries
- frontend unit tests for auth flow, workspace state, review state, export actions
- integration tests for end-to-end project pipeline with fake providers

## Implementation Direction

Use a greenfield app in `/opt/Paper` and reuse only the proven KBF authentication patterns from adjacent repositories. Avoid forcing the system into the structure of `Paper2Slides`, because the manuscript review model is different enough to justify a dedicated architecture.
