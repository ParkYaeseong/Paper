# Paper Role-Aware Intake Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add user-selected upload roles, full-text narrative ingestion, and separate results-table handling so planning and drafting use the right context instead of a preview-only blended profile.

**Architecture:** Persist an explicit role on each artifact, add a new artifact-chunk persistence layer for full-text narrative and supporting documents, and rebuild `DatasetProfile.summary_json` into layered context sections. Update planning and drafting so they consume role-aware context, and update the upload UI so users can assign and edit roles directly.

**Tech Stack:** FastAPI, SQLAlchemy, React, Vitest, pytest, existing Paper storage pipeline

---

### Task 1: Add artifact role persistence and API coverage

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/schemas/project.py`
- Modify: `backend/app/api/routes/projects.py`
- Modify: `backend/app/api/routes/workspace.py`
- Test: `backend/tests/test_projects_api.py`

**Step 1: Write the failing test**

Add tests that prove:

- artifact upload accepts a role for each file
- uploaded artifacts return `metadata_json.role`
- an existing artifact role can be updated after upload

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q backend/tests/test_projects_api.py
```

Expected: FAIL because upload requests do not accept roles and artifact responses do not expose them.

**Step 3: Write minimal implementation**

Implement:

- artifact role persistence through `Artifact.metadata_json["role"]`
- request parsing for per-file roles during upload
- a role-update endpoint for existing artifacts
- role serialization in project and workspace payloads

**Step 4: Run test to verify it passes**

Run the same command and confirm the new upload/update behavior passes.

**Step 5: Commit**

```bash
git add backend/app/models.py backend/app/schemas/project.py backend/app/api/routes/projects.py backend/app/api/routes/workspace.py backend/tests/test_projects_api.py
git commit -m "feat: persist upload roles on artifacts"
```

### Task 2: Add full-text chunk persistence for narrative artifacts

**Files:**
- Modify: `backend/app/models.py`
- Create: `backend/app/services/artifact_chunks.py`
- Create: `backend/tests/test_normalization.py`
- Test: `backend/tests/test_models.py`

**Step 1: Write the failing test**

Add tests that prove:

- a markdown narrative file is split into chunk records rather than reduced to a preview
- chunk records preserve artifact linkage, order, and role

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q backend/tests/test_normalization.py backend/tests/test_models.py
```

Expected: FAIL because no artifact-chunk model or chunking service exists.

**Step 3: Write minimal implementation**

Add an `ArtifactChunk` model and a helper service that:

- reads full text for `.md`, `.txt`, and `.json`
- normalizes whitespace
- splits by headings where possible
- emits ordered chunk rows

**Step 4: Run test to verify it passes**

Run the same pytest command and confirm chunk persistence works.

**Step 5: Commit**

```bash
git add backend/app/models.py backend/app/services/artifact_chunks.py backend/tests/test_normalization.py backend/tests/test_models.py
git commit -m "feat: add full-text artifact chunk persistence"
```

### Task 3: Rebuild ingest as role-aware context generation

**Files:**
- Modify: `backend/app/services/normalization.py`
- Modify: `backend/tests/test_normalization.py`
- Modify: `backend/tests/test_pipeline_api.py`

**Step 1: Write the failing test**

Add tests that prove:

- `narrative_brief` contributes to `narrative_context`
- `supporting_doc` contributes to `supporting_context`
- `results_table` contributes to `results_context`
- the old preview-only note behavior is no longer the main narrative path

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q backend/tests/test_normalization.py backend/tests/test_pipeline_api.py
```

Expected: FAIL because `DatasetProfile.summary_json` still uses one blended summary shape.

**Step 3: Write minimal implementation**

Refactor ingest to produce layered context:

- `project_brief`
- `narrative_context`
- `supporting_context`
- `results_context`
- `background_context`

Keep CSV summary support, but route prose and table artifacts through different summarizers.

**Step 4: Run test to verify it passes**

Run the same command and confirm the new dataset profile structure is produced.

**Step 5: Commit**

```bash
git add backend/app/services/normalization.py backend/tests/test_normalization.py backend/tests/test_pipeline_api.py
git commit -m "feat: build role-aware ingest context"
```

### Task 4: Make planning use role-aware context and system-paper heuristics

**Files:**
- Modify: `backend/app/services/planning.py`
- Modify: `backend/tests/test_pipeline_api.py`

**Step 1: Write the failing test**

Add tests that prove:

- planning prioritizes `narrative_brief` content over `supporting_doc`
- a system/platform-style brief produces a system-paper-style outline
- README-style supporting text does not override the main framing

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q backend/tests/test_pipeline_api.py
```

Expected: FAIL because planning still consumes one blended `summary_json` payload.

**Step 3: Write minimal implementation**

Update planning prompts and fallback behavior to:

- use layered context fields explicitly
- extract distinctive contribution bullets from `narrative_context`
- bias toward system-paper sections when the brief indicates a systems contribution

**Step 4: Run test to verify it passes**

Run the same pytest command and confirm the role-aware outline behavior passes.

**Step 5: Commit**

```bash
git add backend/app/services/planning.py backend/tests/test_pipeline_api.py
git commit -m "feat: make planning role-aware"
```

### Task 5: Make drafting section-aware by source type

**Files:**
- Modify: `backend/app/services/drafting.py`
- Modify: `backend/tests/test_pipeline_api.py`
- Modify: `backend/tests/test_quality.py`

**Step 1: Write the failing test**

Add tests that prove:

- `Introduction` uses narrative/supporting context
- `Methods` or `System Overview` uses supporting/system chunks
- `Results` prefers structured `results_context`
- drafts without `results_table` inputs fall back to weaker results wording and remain auditable

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q backend/tests/test_pipeline_api.py backend/tests/test_quality.py
```

Expected: FAIL because drafting still passes the full dataset profile indiscriminately to each section prompt.

**Step 3: Write minimal implementation**

Refactor section prompts so each section receives only the relevant context slices and extracted contribution bullets.

**Step 4: Run test to verify it passes**

Run the same pytest command and confirm section-aware drafting passes.

**Step 5: Commit**

```bash
git add backend/app/services/drafting.py backend/tests/test_pipeline_api.py backend/tests/test_quality.py
git commit -m "feat: draft sections from role-aware context"
```

### Task 6: Add upload-role selection and editing UI

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/components/UploadPanel.tsx`
- Modify: `frontend/src/components/UploadPanel.test.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Write the failing test**

Add tests that prove:

- users can assign a role before upload
- uploaded artifacts show their role
- users can change a role after upload
- changing a role triggers stale-ingest messaging

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/frontend && npm test -- --run src/components/UploadPanel.test.tsx src/App.test.tsx
```

Expected: FAIL because the upload UI has no role selector and no role-edit path.

**Step 3: Write minimal implementation**

Update the upload panel to:

- track per-file selected roles before upload
- send role metadata with the upload request
- display artifact roles with editable controls
- show ingest-stale guidance when artifact roles change

**Step 4: Run test to verify it passes**

Run the same frontend test command and confirm the upload-role flow passes.

**Step 5: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api.ts frontend/src/components/UploadPanel.tsx frontend/src/components/UploadPanel.test.tsx frontend/src/App.tsx
git commit -m "feat: add upload role selection and editing"
```

### Task 7: Verify end-to-end role-aware intake behavior

**Files:**
- Modify: `backend/tests/test_pipeline_api.py`
- Modify: `frontend/src/App.test.tsx`
- Modify: `README.md`

**Step 1: Write the failing test**

Add an end-to-end test that uploads:

- one `narrative_brief`
- one `supporting_doc`
- one `results_table`

Then verify planning and drafting reflect the intended prioritization.

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q backend/tests/test_pipeline_api.py
cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx
```

Expected: FAIL until the whole role-aware flow is wired through.

**Step 3: Write minimal implementation**

Complete any remaining wiring, then update the README to explain:

- which role to choose for each upload type
- why results tables are processed separately
- when to rerun ingest after changing roles

**Step 4: Run test to verify it passes**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q
cd /opt/Paper/frontend && npm test -- --run
cd /opt/Paper/frontend && npm run build
```

Expected: backend tests pass, frontend tests pass, frontend build succeeds.

**Step 5: Commit**

```bash
git add backend/tests/test_pipeline_api.py frontend/src/App.test.tsx README.md
git commit -m "docs: explain role-aware intake workflow"
```
