# Paper Quality, Run All, and Figure Generation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a guided `Run All` workflow, a persistent quality audit and final-export gate, and automatic PaperBanana-based figure generation for review-ready manuscripts.

**Architecture:** Extend the backend pipeline with `quality`, `figures`, and `run_all` stages. Persist quality findings and figure-generation artifacts in the database, expose them through workspace APIs, and update the frontend so the default path is upload -> run all -> review -> export while manual stage controls move into an advanced panel.

**Tech Stack:** FastAPI, SQLAlchemy, RQ/Redis workers, React, Vitest, pytest, python-docx, PaperBanana local runtime

---

### Task 1: Add backend red tests for quality, figures, and run_all

**Files:**
- Modify: `backend/tests/test_pipeline_api.py`
- Create: `backend/tests/test_quality.py`
- Create: `backend/tests/test_figures.py`

**Step 1: Write the failing test**

Add tests that cover:

- `run_all` triggers `ingest -> plan -> draft -> evidence -> quality -> figures`
- `quality` produces critical issues for unresolved placeholders and missing citations
- `figures` creates figure specs from draft placeholders
- `Final Export` is blocked when critical issues exist

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q tests/test_pipeline_api.py tests/test_quality.py tests/test_figures.py
```

Expected: FAIL because the new stages, models, and export rules do not exist yet.

**Step 3: Write minimal implementation**

Implement only enough backend stage registration and stub behavior to satisfy the first failures.

**Step 4: Run test to verify it passes**

Run the same command and confirm the initial stage-recognition failures are resolved.

**Step 5: Commit**

```bash
git add backend/tests/test_pipeline_api.py backend/tests/test_quality.py backend/tests/test_figures.py
git commit -m "test: add quality and figure pipeline coverage"
```

### Task 2: Add database models for quality and figures

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/db.py`
- Test: `backend/tests/test_quality.py`
- Test: `backend/tests/test_figures.py`

**Step 1: Write the failing test**

Extend the new tests to assert that `QualityReport`, `FigureSpec`, and `FigureAsset` rows can be created and linked to projects.

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q tests/test_quality.py tests/test_figures.py
```

Expected: FAIL with missing model or table errors.

**Step 3: Write minimal implementation**

Add:

- `QualityReport`
- `FigureSpec`
- `FigureAsset`

with project relationships and timestamp handling consistent with the existing models.

**Step 4: Run test to verify it passes**

Run the same pytest command and confirm model persistence passes.

**Step 5: Commit**

```bash
git add backend/app/models.py backend/app/db.py backend/tests/test_quality.py backend/tests/test_figures.py
git commit -m "feat: add quality and figure persistence models"
```

### Task 3: Implement quality audit service

**Files:**
- Create: `backend/app/services/quality.py`
- Modify: `backend/app/services/exporting.py`
- Modify: `backend/app/api/routes/workspace.py`
- Test: `backend/tests/test_quality.py`

**Step 1: Write the failing test**

Add tests for:

- unresolved citation tokens become critical issues
- `[manual review]` becomes a critical issue
- unresolved figure placeholders become critical issues
- generic-results heuristics create warnings
- `submission_ready` is false when critical issues exist

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q tests/test_quality.py
```

Expected: FAIL because no quality service or report serialization exists yet.

**Step 3: Write minimal implementation**

- Create a `run_quality_audit(session, project)` service
- Inspect the latest draft sections, citation slots, evidence matches, and rendered export text
- Persist a new `QualityReport`
- Expose the latest report in the workspace payload

**Step 4: Run test to verify it passes**

Run the same pytest command and confirm the report contents match expectations.

**Step 5: Commit**

```bash
git add backend/app/services/quality.py backend/app/services/exporting.py backend/app/api/routes/workspace.py backend/tests/test_quality.py
git commit -m "feat: add manuscript quality audit"
```

### Task 4: Implement figure spec generation and PaperBanana adapter

**Files:**
- Create: `backend/app/services/figures.py`
- Create: `backend/app/services/paperbanana_adapter.py`
- Modify: `backend/app/services/storage.py`
- Test: `backend/tests/test_figures.py`

**Step 1: Write the failing test**

Add tests for:

- placeholder extraction creates figure specs with correct section linkage
- mocked PaperBanana execution produces figure assets
- stored candidate files are linked as artifacts

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q tests/test_figures.py
```

Expected: FAIL because no figure service or adapter exists.

**Step 3: Write minimal implementation**

- Parse figure placeholders from draft content
- Build `FigureSpec` rows
- Implement a local adapter that shells out to PaperBanana or a wrapper command
- Normalize generated files into `Artifact` and `FigureAsset` rows

**Step 4: Run test to verify it passes**

Run the same pytest command and confirm the mocked adapter path passes.

**Step 5: Commit**

```bash
git add backend/app/services/figures.py backend/app/services/paperbanana_adapter.py backend/app/services/storage.py backend/tests/test_figures.py
git commit -m "feat: add PaperBanana figure generation adapter"
```

### Task 5: Add pipeline orchestration for quality, figures, and run_all

**Files:**
- Modify: `backend/app/services/pipeline_runner.py`
- Modify: `backend/app/jobs.py`
- Modify: `backend/app/queue.py`
- Test: `backend/tests/test_pipeline_api.py`

**Step 1: Write the failing test**

Expand the pipeline tests to assert:

- `quality`, `figures`, and `run_all` are accepted stages
- `run_all` runs stages in order
- failure in `quality` or `figures` halts later work
- job results record the terminal sub-stage

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q tests/test_pipeline_api.py
```

Expected: FAIL because the orchestrator stages do not exist.

**Step 3: Write minimal implementation**

- Add stage metadata and prerequisites
- Implement `run_all` orchestration in the worker path
- Ensure sequential execution with clear job logging
- Keep manual stage execution available

**Step 4: Run test to verify it passes**

Run the same pytest command and confirm orchestration behavior passes.

**Step 5: Commit**

```bash
git add backend/app/services/pipeline_runner.py backend/app/jobs.py backend/app/queue.py backend/tests/test_pipeline_api.py
git commit -m "feat: add run-all orchestration and quality stages"
```

### Task 6: Split export into draft and final modes

**Files:**
- Modify: `backend/app/services/exporting.py`
- Modify: `backend/app/api/routes/workspace.py`
- Modify: `backend/tests/test_exporting.py`
- Test: `backend/tests/test_quality.py`

**Step 1: Write the failing test**

Add tests for:

- draft export succeeds even with critical issues
- final export fails with a clear error when `submission_ready` is false
- selected figure assets are included in export manifests

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q tests/test_exporting.py tests/test_quality.py
```

Expected: FAIL because export mode and blocking behavior do not exist.

**Step 3: Write minimal implementation**

- Add export mode support to the export service and routes
- Gate final export on the latest quality report
- Include selected figure assets in markdown/json/docx outputs

**Step 4: Run test to verify it passes**

Run the same pytest command and confirm export behavior passes.

**Step 5: Commit**

```bash
git add backend/app/services/exporting.py backend/app/api/routes/workspace.py backend/tests/test_exporting.py backend/tests/test_quality.py
git commit -m "feat: gate final export on quality report"
```

### Task 7: Add frontend red tests for Run All, quality summary, and figure review

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Create: `frontend/src/components/QualitySummaryPanel.test.tsx`
- Create: `frontend/src/components/FigureReviewPanel.test.tsx`

**Step 1: Write the failing test**

Add tests that cover:

- `Run All` is the main action
- manual stage buttons are behind an `Advanced` toggle
- quality summary shows critical and warning counts
- final export is disabled when blocked
- figure candidates can be selected

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/frontend && npm test -- --run
```

Expected: FAIL because the UI still exposes the old control structure.

**Step 3: Write minimal implementation**

Implement only enough UI structure to satisfy the tests.

**Step 4: Run test to verify it passes**

Run the same Vitest command and confirm the new assertions pass.

**Step 5: Commit**

```bash
git add frontend/src/App.test.tsx frontend/src/components/QualitySummaryPanel.test.tsx frontend/src/components/FigureReviewPanel.test.tsx
git commit -m "test: add run-all and review UI coverage"
```

### Task 8: Implement Run All and advanced manual controls in the frontend

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ProjectWorkspace.tsx`
- Modify: `frontend/src/components/UploadPanel.tsx`
- Modify: `frontend/src/components/OutlinePanel.tsx`
- Modify: `frontend/src/components/DraftPanel.tsx`
- Modify: `frontend/src/components/EvidenceReviewPanel.tsx`
- Modify: `frontend/src/components/ExportPanel.tsx`
- Modify: `frontend/src/lib/stages.ts`

**Step 1: Write the failing test**

Use the red tests from Task 7.

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/frontend && npm test -- --run
```

Expected: FAIL

**Step 3: Write minimal implementation**

- Add `Run All`
- Move manual stage buttons behind `Advanced`
- Track `run_all`, `quality`, and `figures` in stage metadata
- Keep the floating job status bar compatible with orchestration jobs

**Step 4: Run test to verify it passes**

Run the same Vitest command and confirm the new structure passes.

**Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/ProjectWorkspace.tsx frontend/src/components/UploadPanel.tsx frontend/src/components/OutlinePanel.tsx frontend/src/components/DraftPanel.tsx frontend/src/components/EvidenceReviewPanel.tsx frontend/src/components/ExportPanel.tsx frontend/src/lib/stages.ts
git commit -m "feat: add run-all workflow and advanced controls"
```

### Task 9: Implement quality summary and figure review panels

**Files:**
- Create: `frontend/src/components/QualitySummaryPanel.tsx`
- Create: `frontend/src/components/FigureReviewPanel.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/components/QualitySummaryPanel.test.tsx`
- Test: `frontend/src/components/FigureReviewPanel.test.tsx`

**Step 1: Write the failing test**

Use the new component tests to cover:

- issue counts and readiness state
- recommended actions rendering
- figure candidate selection
- regenerate action visibility

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/frontend && npm test -- --run src/components/QualitySummaryPanel.test.tsx src/components/FigureReviewPanel.test.tsx
```

Expected: FAIL because the components do not exist.

**Step 3: Write minimal implementation**

- Build `QualitySummaryPanel`
- Build `FigureReviewPanel`
- Style them consistently with the existing workspace panels

**Step 4: Run test to verify it passes**

Run the same Vitest command and confirm both components pass.

**Step 5: Commit**

```bash
git add frontend/src/components/QualitySummaryPanel.tsx frontend/src/components/FigureReviewPanel.tsx frontend/src/styles.css frontend/src/components/QualitySummaryPanel.test.tsx frontend/src/components/FigureReviewPanel.test.tsx
git commit -m "feat: add quality summary and figure review panels"
```

### Task 10: Verify end-to-end behavior and update docs

**Files:**
- Modify: `frontend/src/lib/guide-content.ts`
- Modify: `README.md`
- Modify: `docs/plans/2026-03-24-paper-authoring-design.md` if cross-reference notes are needed

**Step 1: Write the failing test**

Adjust help-copy assertions to expect:

- upload -> run all -> review -> export flow
- draft export vs final export distinction
- figure review language

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx
```

Expected: FAIL if the guide still describes the old stage-heavy flow.

**Step 3: Write minimal implementation**

- Update in-app guide copy
- Update README usage flow and PaperBanana dependency notes
- Keep docs scoped to the implemented behavior

**Step 4: Run test to verify it passes**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q
cd /opt/Paper/frontend && npm test -- --run
cd /opt/Paper/frontend && npm run build
cd /opt/Paper && docker compose ps
curl -sS -o /dev/null -w '%{http_code}\n' https://paper.k-biofoundrycopilot.duckdns.org/
curl -sS -o /dev/null -w '%{http_code}\n' https://paper.k-biofoundrycopilot.duckdns.org/api/auth/oidc/config
```

Expected:

- backend tests pass
- frontend tests pass
- frontend build passes
- containers are healthy
- both public endpoints return `200`

**Step 5: Commit**

```bash
git add frontend/src/lib/guide-content.ts README.md
git commit -m "docs: update guided run-all manuscript workflow"
```
