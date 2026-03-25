# Paper Job Feedback Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Collapse retrieval and grounding into one user-facing evidence action and make job execution state obvious through inline button feedback and a global floating status bar.

**Architecture:** Add a backend `evidence` pipeline stage so the browser can trigger one job instead of chaining two async jobs itself. In the frontend, centralize stage metadata and derive both button labels and the global job banner from the active and recently completed jobs already returned by polling.

**Tech Stack:** FastAPI, SQLAlchemy, React, Vitest, pytest

---

### Task 1: Add backend coverage for the new evidence stage

**Files:**
- Modify: `backend/tests/test_pipeline_api.py`

**Step 1: Write the failing test**

Extend the end-to-end pipeline test so the stage list uses `evidence` instead of separate `retrieve` and `ground`, and assert that evidence matches still exist after export.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && . .venv/bin/activate && pytest -q tests/test_pipeline_api.py`
Expected: FAIL because `evidence` is an unknown stage.

**Step 3: Write minimal implementation**

Update backend pipeline stage validation and execution to recognize `evidence`.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && . .venv/bin/activate && pytest -q tests/test_pipeline_api.py`
Expected: PASS

### Task 2: Implement backend evidence orchestration

**Files:**
- Modify: `backend/app/services/pipeline_runner.py`

**Step 1: Write the failing test**

Use the failing pipeline API test from Task 1 as the red test.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && . .venv/bin/activate && pytest -q tests/test_pipeline_api.py`
Expected: FAIL with unknown stage or prerequisite failure.

**Step 3: Write minimal implementation**

- Add `evidence` to `PIPELINE_STAGES`
- Allow `ensure_stage_prerequisites()` to gate `evidence` on citation slots existing
- Make `run_pipeline_stage()` execute `run_retrieve()` followed by `run_grounding()`
- Ensure `process_pipeline_job()` serializes the result cleanly for list-like return values

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && . .venv/bin/activate && pytest -q tests/test_pipeline_api.py`
Expected: PASS

### Task 3: Add failing frontend tests for evidence UX and global job feedback

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Create or modify: `frontend/src/components/ExportPanel.test.tsx`

**Step 1: Write the failing test**

Add tests for:
- `Run Evidence` replacing `Run Retrieve` and `Run Ground`
- active stage buttons showing `Running...`
- a global floating status bar appearing during active jobs and showing success after polling completes

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- --run`
Expected: FAIL because the UI still shows the old buttons and no global status bar exists.

**Step 3: Write minimal implementation**

Implement the frontend changes required by the tests without extra UI features.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/frontend && npm test -- --run`
Expected: PASS

### Task 4: Implement global stage metadata and inline running labels

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/UploadPanel.tsx`
- Modify: `frontend/src/components/OutlinePanel.tsx`
- Modify: `frontend/src/components/DraftPanel.tsx`
- Modify: `frontend/src/components/EvidenceReviewPanel.tsx`
- Modify: `frontend/src/components/ExportPanel.tsx`
- Create: `frontend/src/lib/stages.ts`

**Step 1: Write the failing test**

Use the new App/Vitest expectations from Task 3.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- --run`
Expected: FAIL

**Step 3: Write minimal implementation**

- Add shared stage label helpers in `frontend/src/lib/stages.ts`
- Switch evidence panel to a single `Run Evidence` button
- Make buttons render `Running...` for their active stage
- Remove the export-panel job strip
- Derive a global active/latest job notice from polled jobs

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/frontend && npm test -- --run`
Expected: PASS

### Task 5: Add the floating status bar UI

**Files:**
- Create: `frontend/src/components/JobStatusBar.tsx`
- Modify: `frontend/src/components/Header.tsx`
- Modify: `frontend/src/styles.css`

**Step 1: Write the failing test**

Use the App-level tests from Task 3 that assert the bar content and success transition.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

- Add a non-blocking floating status bar near the top of the app
- Show current stage label, status label, and error detail on failure
- Auto-hide terminal success after a short delay while keeping failures visible

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx`
Expected: PASS

### Task 6: Update help copy and verify the full app

**Files:**
- Modify: `frontend/src/lib/guide-content.ts`
- Modify: `frontend/src/App.test.tsx`
- Modify: `backend/tests/test_pipeline_api.py`

**Step 1: Write the failing test**

Adjust tests to expect `Run Evidence` in guide copy and pipeline behavior.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- --run`
Expected: FAIL if stale guide text still references retrieve/ground separately.

**Step 3: Write minimal implementation**

Update the guide text and any stale labels to match the new workflow.

**Step 4: Run test to verify it passes**

Run:
- `cd /opt/Paper/backend && . .venv/bin/activate && pytest -q`
- `cd /opt/Paper/frontend && npm test -- --run`
- `cd /opt/Paper/frontend && npm run build`

Expected: all pass
