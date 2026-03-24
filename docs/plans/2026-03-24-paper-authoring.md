# Paper Authoring System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a KBF SSO-protected manuscript authoring web app in `/opt/Paper` with upload, planning, draft generation, literature retrieval, citation grounding, review UI, and export support.

**Architecture:** A greenfield FastAPI + React/Vite application with Postgres as the system of record, Redis-backed job orchestration, a Python worker for long-running stages, and KBF Keycloak OIDC authentication copied from proven adjacent services. The backend persists canonical manuscript state as structured JSON plus section records and evidence mappings, while the frontend provides a project workspace spanning upload, drafting, grounding review, and export.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis, RQ, Pydantic, React, TypeScript, Vite, Vitest, React Testing Library, OpenAI API, Gemini API

---

### Task 1: Initialize repository structure

**Files:**
- Create: `/opt/Paper/.gitignore`
- Create: `/opt/Paper/README.md`
- Create: `/opt/Paper/backend/pyproject.toml`
- Create: `/opt/Paper/backend/app/__init__.py`
- Create: `/opt/Paper/backend/tests/__init__.py`
- Create: `/opt/Paper/frontend/package.json`
- Create: `/opt/Paper/frontend/tsconfig.json`
- Create: `/opt/Paper/frontend/vite.config.ts`
- Create: `/opt/Paper/frontend/src/main.tsx`
- Create: `/opt/Paper/frontend/src/App.tsx`
- Create: `/opt/Paper/docker-compose.yml`

**Step 1: Write the failing test**

Create a backend smoke test that imports the FastAPI app factory and expects it to return an app with a health route.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_app_smoke.py -q`
Expected: FAIL because the app factory does not exist yet.

**Step 3: Write minimal implementation**

Create the base backend package, app factory, and frontend bootstrap files.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_app_smoke.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add .
git commit -m "chore: initialize paper authoring app skeleton"
```

### Task 2: Add backend settings and health API

**Files:**
- Create: `/opt/Paper/backend/app/config.py`
- Create: `/opt/Paper/backend/app/main.py`
- Create: `/opt/Paper/backend/app/api/__init__.py`
- Create: `/opt/Paper/backend/app/api/routes/__init__.py`
- Create: `/opt/Paper/backend/app/api/routes/health.py`
- Create: `/opt/Paper/backend/tests/test_health_api.py`

**Step 1: Write the failing test**

Write a test asserting `GET /api/healthz` returns `200` and a JSON payload with app metadata.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_health_api.py -q`
Expected: FAIL because the route is missing.

**Step 3: Write minimal implementation**

Add settings loading and mount the health router.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_health_api.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend
git commit -m "feat: add backend settings and health route"
```

### Task 3: Add OIDC auth and session handling

**Files:**
- Create: `/opt/Paper/backend/app/auth.py`
- Create: `/opt/Paper/backend/app/deps.py`
- Create: `/opt/Paper/backend/app/api/routes/auth.py`
- Create: `/opt/Paper/backend/tests/test_auth_api.py`
- Create: `/opt/Paper/frontend/src/lib/auth.ts`
- Create: `/opt/Paper/frontend/src/lib/auth.test.ts`

**Step 1: Write the failing test**

Write backend tests for:
- OIDC config exposure
- session cookie issuance from callback exchange
- protected route rejection without session

Write frontend tests for:
- callback param parsing
- redirect URI generation

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_auth_api.py -q`
Expected: FAIL because auth routes and helpers do not exist.

Run: `cd /opt/Paper/frontend && npm test -- src/lib/auth.test.ts`
Expected: FAIL because the auth helpers do not exist.

**Step 3: Write minimal implementation**

Copy and adapt the Paper2Slides OIDC/session pattern to the new `paper` client and expose auth endpoints for the SPA.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_auth_api.py -q`
Expected: PASS

Run: `cd /opt/Paper/frontend && npm test -- src/lib/auth.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend frontend
git commit -m "feat: add KBF OIDC auth for paper app"
```

### Task 4: Add database models and migration baseline

**Files:**
- Create: `/opt/Paper/backend/alembic.ini`
- Create: `/opt/Paper/backend/alembic/env.py`
- Create: `/opt/Paper/backend/alembic/versions/20260324_0001_initial_schema.py`
- Create: `/opt/Paper/backend/app/db.py`
- Create: `/opt/Paper/backend/app/models.py`
- Create: `/opt/Paper/backend/tests/test_models.py`

**Step 1: Write the failing test**

Write tests that create tables in a temporary database and assert the presence of:
- projects
- artifacts
- dataset_profiles
- outlines
- draft_sections
- citation_slots
- reference_records
- evidence_matches
- review_decisions
- export_bundles
- job_runs

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_models.py -q`
Expected: FAIL because the models and metadata do not exist.

**Step 3: Write minimal implementation**

Add the ORM models, metadata, and migration baseline.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_models.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend
git commit -m "feat: add manuscript persistence schema"
```

### Task 5: Add project CRUD and artifact upload APIs

**Files:**
- Create: `/opt/Paper/backend/app/schemas/project.py`
- Create: `/opt/Paper/backend/app/services/storage.py`
- Create: `/opt/Paper/backend/app/api/routes/projects.py`
- Create: `/opt/Paper/backend/tests/test_projects_api.py`

**Step 1: Write the failing test**

Write tests for:
- creating a project
- listing only the current user's projects
- uploading artifacts to a project
- rejecting access to other users' projects

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_projects_api.py -q`
Expected: FAIL because project APIs do not exist.

**Step 3: Write minimal implementation**

Add protected CRUD routes and file storage helpers.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_projects_api.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend
git commit -m "feat: add project and artifact APIs"
```

### Task 6: Add pipeline service contracts and job runner

**Files:**
- Create: `/opt/Paper/backend/app/jobs.py`
- Create: `/opt/Paper/backend/app/queue.py`
- Create: `/opt/Paper/backend/app/services/pipeline_types.py`
- Create: `/opt/Paper/backend/app/services/pipeline_runner.py`
- Create: `/opt/Paper/backend/app/api/routes/jobs.py`
- Create: `/opt/Paper/backend/tests/test_jobs_api.py`

**Step 1: Write the failing test**

Write tests for:
- enqueueing pipeline stages
- tracking stage state
- polling job status
- rejecting duplicate active runs for the same stage/project

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_jobs_api.py -q`
Expected: FAIL because the job system does not exist.

**Step 3: Write minimal implementation**

Add the queue abstraction, `JobRun` state transitions, and stage enqueue endpoints.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_jobs_api.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend
git commit -m "feat: add pipeline job orchestration"
```

### Task 7: Add normalization and manuscript planning stages

**Files:**
- Create: `/opt/Paper/backend/app/services/llm_clients.py`
- Create: `/opt/Paper/backend/app/services/normalization.py`
- Create: `/opt/Paper/backend/app/services/planning.py`
- Create: `/opt/Paper/backend/app/api/routes/workspace.py`
- Create: `/opt/Paper/backend/tests/test_planning_service.py`

**Step 1: Write the failing test**

Write tests that, given fake artifacts and fake LLM providers, assert:
- a dataset profile is created
- an outline is generated
- citation slots are produced for claims needing evidence

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_planning_service.py -q`
Expected: FAIL because planning services do not exist.

**Step 3: Write minimal implementation**

Implement normalization and planning with deterministic fake provider support for tests.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_planning_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend
git commit -m "feat: add normalization and planning stages"
```

### Task 8: Add draft generation stage

**Files:**
- Create: `/opt/Paper/backend/app/services/drafting.py`
- Create: `/opt/Paper/backend/tests/test_drafting_service.py`

**Step 1: Write the failing test**

Write tests asserting draft generation:
- creates section records
- preserves placeholder slots
- versions a section on regeneration

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_drafting_service.py -q`
Expected: FAIL because drafting does not exist.

**Step 3: Write minimal implementation**

Implement section drafting using structured prompt contracts and per-section persistence.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_drafting_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend
git commit -m "feat: add section drafting stage"
```

### Task 9: Add literature retrieval and reference normalization

**Files:**
- Create: `/opt/Paper/backend/app/services/retrieval.py`
- Create: `/opt/Paper/backend/app/services/references.py`
- Create: `/opt/Paper/backend/tests/test_retrieval_service.py`

**Step 1: Write the failing test**

Write tests asserting retrieval:
- generates claim queries
- merges duplicate records from multiple sources
- stores normalized reference records

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_retrieval_service.py -q`
Expected: FAIL because retrieval services do not exist.

**Step 3: Write minimal implementation**

Implement PubMed/OpenAlex retrieval interfaces with fake adapters for tests and metadata normalization logic.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_retrieval_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend
git commit -m "feat: add literature retrieval and reference normalization"
```

### Task 10: Add evidence grounding and citation insertion

**Files:**
- Create: `/opt/Paper/backend/app/services/grounding.py`
- Create: `/opt/Paper/backend/tests/test_grounding_service.py`

**Step 1: Write the failing test**

Write tests asserting grounding:
- scores support for each claim slot
- selects supporting papers only above threshold
- marks weak or unsupported claims correctly
- renders references back into manuscript text

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_grounding_service.py -q`
Expected: FAIL because grounding does not exist.

**Step 3: Write minimal implementation**

Implement support scoring, evidence selection, status assignment, and citation rendering.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_grounding_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend
git commit -m "feat: add evidence grounding and citation rendering"
```

### Task 11: Add export services

**Files:**
- Create: `/opt/Paper/backend/app/services/exporting.py`
- Create: `/opt/Paper/backend/tests/test_exporting_service.py`

**Step 1: Write the failing test**

Write tests asserting export generation for:
- canonical manuscript JSON
- Markdown
- BibTeX
- DOCX

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_exporting_service.py -q`
Expected: FAIL because exporting does not exist.

**Step 3: Write minimal implementation**

Implement export builders and file bundle persistence.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_exporting_service.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend
git commit -m "feat: add manuscript export services"
```

### Task 12: Add project workspace UI shell

**Files:**
- Create: `/opt/Paper/frontend/src/lib/api.ts`
- Create: `/opt/Paper/frontend/src/lib/types.ts`
- Create: `/opt/Paper/frontend/src/components/AppShell.tsx`
- Create: `/opt/Paper/frontend/src/components/ProjectList.tsx`
- Create: `/opt/Paper/frontend/src/components/ProjectWorkspace.tsx`
- Create: `/opt/Paper/frontend/src/components/Header.tsx`
- Create: `/opt/Paper/frontend/src/styles.css`
- Create: `/opt/Paper/frontend/src/App.test.tsx`

**Step 1: Write the failing test**

Write UI tests asserting:
- unauthenticated users see a login gate
- authenticated users see a project list
- selecting a project opens the workspace shell

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- src/App.test.tsx`
Expected: FAIL because the UI shell does not exist.

**Step 3: Write minimal implementation**

Build the authenticated shell and project navigation.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/frontend && npm test -- src/App.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add frontend
git commit -m "feat: add paper workspace shell"
```

### Task 13: Add upload, outline, and draft UI

**Files:**
- Create: `/opt/Paper/frontend/src/components/UploadPanel.tsx`
- Create: `/opt/Paper/frontend/src/components/OutlinePanel.tsx`
- Create: `/opt/Paper/frontend/src/components/DraftPanel.tsx`
- Create: `/opt/Paper/frontend/src/components/JobTimeline.tsx`
- Create: `/opt/Paper/frontend/src/components/UploadPanel.test.tsx`

**Step 1: Write the failing test**

Write UI tests asserting:
- files can be queued for upload
- outline results render after planning
- section drafts render with placeholder markers

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- src/components/UploadPanel.test.tsx`
Expected: FAIL because the panels do not exist.

**Step 3: Write minimal implementation**

Add upload, outline, draft, and stage status components.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/frontend && npm test -- src/components/UploadPanel.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add frontend
git commit -m "feat: add upload and draft workflow UI"
```

### Task 14: Add evidence review and reference manager UI

**Files:**
- Create: `/opt/Paper/frontend/src/components/EvidenceReviewPanel.tsx`
- Create: `/opt/Paper/frontend/src/components/ReferencePanel.tsx`
- Create: `/opt/Paper/frontend/src/components/EvidenceReviewPanel.test.tsx`

**Step 1: Write the failing test**

Write UI tests asserting:
- claim rows render status badges
- reviewers can accept or reject evidence
- manual review items are clearly marked

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- src/components/EvidenceReviewPanel.test.tsx`
Expected: FAIL because the review UI does not exist.

**Step 3: Write minimal implementation**

Build the sentence-centric evidence review and reference selection panels.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/frontend && npm test -- src/components/EvidenceReviewPanel.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add frontend
git commit -m "feat: add evidence review UI"
```

### Task 15: Add export UI and end-to-end local composition

**Files:**
- Create: `/opt/Paper/frontend/src/components/ExportPanel.tsx`
- Create: `/opt/Paper/frontend/src/components/ExportPanel.test.tsx`
- Modify: `/opt/Paper/docker-compose.yml`
- Create: `/opt/Paper/backend/Dockerfile`
- Create: `/opt/Paper/frontend/Dockerfile`

**Step 1: Write the failing test**

Write UI tests asserting:
- export actions are visible after successful grounding
- download links render for generated bundles

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- src/components/ExportPanel.test.tsx`
Expected: FAIL because export UI does not exist.

**Step 3: Write minimal implementation**

Add export UI and local compose services for app, database, cache, and worker.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/frontend && npm test -- src/components/ExportPanel.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add .
git commit -m "feat: add export UI and local compose stack"
```

### Task 16: Wire KBF infra and deployment docs

**Files:**
- Create: `/opt/Paper/deploy/README.md`
- Create: `/opt/Paper/deploy/paper.env.example`
- Create: `/opt/Paper/deploy/paper.service.example`
- Modify: `/opt/kbf-infra/keycloak/import/kbf-realm.template.json`
- Modify: `/opt/kbf-infra/README.md`

**Step 1: Write the failing test**

Write a backend or config test asserting deployment config expectations for the `paper` OIDC client and environment names.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && pytest tests/test_deploy_config.py -q`
Expected: FAIL because the deployment config artifacts do not exist.

**Step 3: Write minimal implementation**

Document deployment, add example env files, and register the `paper` Keycloak client in shared infra.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && pytest tests/test_deploy_config.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add . /opt/kbf-infra/keycloak/import/kbf-realm.template.json /opt/kbf-infra/README.md
git commit -m "feat: add KBF deployment configuration for paper app"
```

### Task 17: Run full verification

**Files:**
- Modify as needed based on failures from prior tasks.

**Step 1: Run backend test suite**

Run: `cd /opt/Paper/backend && pytest -q`
Expected: PASS

**Step 2: Run frontend test suite**

Run: `cd /opt/Paper/frontend && npm test -- --run`
Expected: PASS

**Step 3: Run frontend production build**

Run: `cd /opt/Paper/frontend && npm run build`
Expected: PASS

**Step 4: Run local stack smoke test**

Run: `cd /opt/Paper && docker compose config`
Expected: PASS

**Step 5: Commit final fixes**

```bash
cd /opt/Paper
git add .
git commit -m "chore: finalize paper authoring v1"
```
