# Paper Figure Handoff Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace in-app PaperBanana image generation with figure handoff specs that prepare PaperBanana-ready method text and captions, then expose copy actions in the Figure Review UI.

**Architecture:** Rework the backend `figures` stage so it parses manuscript placeholders into prepared `FigureSpec` records instead of generating assets. Relax quality and export logic so prepared handoff specs satisfy figure requirements. Replace the frontend figure candidate grid with text handoff cards that expose clipboard copy actions.

**Tech Stack:** FastAPI, SQLAlchemy, React, Vitest, pytest, existing Paper workspace API

---

### Task 1: Add backend tests for text-only figure handoff generation

**Files:**
- Modify: `backend/tests/test_figures.py`
- Modify: `backend/tests/test_quality.py`
- Modify: `backend/tests/test_exporting.py`

**Step 1: Write the failing test**

Add tests that prove:

- the `figures` stage creates `FigureSpec` rows with prepared text handoff fields
- no `FigureAsset` rows are created
- prepared figure specs satisfy figure-related quality checks
- final export does not require a selected image asset

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q backend/tests/test_figures.py backend/tests/test_quality.py backend/tests/test_exporting.py
```

Expected: FAIL because the current figure stage still generates image assets and quality still expects a selected asset.

**Step 3: Write minimal implementation**

Implement a prepared handoff flow in the figure service and align the quality/export rules with it.

**Step 4: Run test to verify it passes**

Run the same command and confirm the new text-only behavior passes.

### Task 2: Add a dedicated handoff field to `FigureSpec`

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/api/routes/workspace.py`
- Modify: `frontend/src/lib/types.ts`

**Step 1: Write the failing test**

Extend backend and frontend expectations so serialized figure specs include `method_section_content`.

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q backend/tests/test_figures.py
cd /opt/Paper/frontend && npm test -- --run src/components/FigureReviewPanel.test.tsx
```

Expected: FAIL because the field does not exist in the model or serialized payload.

**Step 3: Write minimal implementation**

Add `method_section_content` to the model and workspace serialization, then type it in the frontend.

**Step 4: Run test to verify it passes**

Run the same commands and confirm the new field is present end-to-end.

### Task 3: Replace backend figure generation with prepared handoff specs

**Files:**
- Modify: `backend/app/services/figures.py`
- Modify: `backend/app/services/quality.py`
- Modify: `backend/app/services/exporting.py`
- Modify: `backend/app/services/paperbanana_adapter.py`

**Step 1: Write the failing test**

Add or extend tests that prove:

- the stage extracts method-friendly context from the draft section
- figure status becomes `prepared`
- no external PaperBanana runtime is invoked by the stage

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q backend/tests/test_figures.py backend/tests/test_exporting.py
```

Expected: FAIL because the service still calls `generate_paperbanana_candidates` and marks specs as `generated`.

**Step 3: Write minimal implementation**

Refactor the figure service to:

- parse placeholders
- create a `method_section_content` handoff field from section context
- stop generating assets
- set figure specs to `prepared`
- treat figure completion as spec existence rather than selected asset existence

**Step 4: Run test to verify it passes**

Run the same command and confirm the handoff stage passes without asset generation.

### Task 4: Replace figure candidate UI with copyable handoff cards

**Files:**
- Modify: `frontend/src/components/FigureReviewPanel.tsx`
- Modify: `frontend/src/components/FigureReviewPanel.test.tsx`
- Modify: `frontend/src/lib/stages.ts`
- Modify: `frontend/src/lib/guide-content.ts`

**Step 1: Write the failing test**

Add tests that prove:

- the panel renders method-section content and caption text
- copy buttons exist for both fields
- the empty state explains the Paper-to-PaperBanana handoff flow

**Step 2: Run test to verify it fails**

Run:
```bash
cd /opt/Paper/frontend && npm test -- --run src/components/FigureReviewPanel.test.tsx
```

Expected: FAIL because the panel still expects image previews and selection buttons.

**Step 3: Write minimal implementation**

Update the panel to render handoff cards and use the Clipboard API with a safe fallback where needed.

**Step 4: Run test to verify it passes**

Run the same command and confirm the new review flow passes.

### Task 5: Verify the end-to-end figure handoff workflow

**Files:**
- Modify: `README.md`

**Step 1: Run verification**

Run:
```bash
cd /opt/Paper/backend && . .venv/bin/activate && pytest -q backend/tests/test_figures.py backend/tests/test_quality.py backend/tests/test_exporting.py
cd /opt/Paper/frontend && npm test -- --run src/components/FigureReviewPanel.test.tsx
cd /opt/Paper/frontend && npm run build
```

Expected: PASS with the figure stage producing copyable handoff specs and no dependency on generated image assets.

**Step 2: Update docs**

Update the README so it explains that:

- Paper prepares figure handoff text
- users generate visuals in PaperBanana manually
- PaperBanana advanced settings stay outside Paper
