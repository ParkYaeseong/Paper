# Paper Async Job Orchestration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert manuscript pipeline execution from synchronous API work into Redis/RQ-backed asynchronous jobs with worker processing and frontend polling.

**Architecture:** The API will validate and enqueue stage work into Redis, persist visible job state in `JobRun`, and return immediately. A separate worker process will execute pipeline stages, update job lifecycle fields, and the frontend will poll job endpoints until completion before refreshing workspace state.

**Tech Stack:** FastAPI, SQLAlchemy, Redis, RQ, React, TypeScript, Vitest, Pytest, Docker Compose

---

### Task 1: Add failing backend tests for queue-backed jobs

**Files:**
- Create: `/opt/Paper/backend/tests/test_jobs_api.py`
- Modify: `/opt/Paper/backend/tests/conftest.py`

**Step 1: Write the failing test**

Write tests for:
- `POST /api/projects/{id}/pipeline/{stage}` returns `202` and `queued`
- duplicate active jobs for the same stage return `409`
- `GET /api/projects/{id}/jobs` returns project jobs
- `GET /api/projects/{id}/jobs/{job_id}` returns one job
- direct worker execution marks a queued job `succeeded`

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && . .venv/bin/activate && pytest tests/test_jobs_api.py -q`
Expected: FAIL because jobs API and worker runner do not exist.

**Step 3: Write minimal implementation**

Add only the minimum fixtures and assertions needed to drive queue and worker behavior.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && . .venv/bin/activate && pytest tests/test_jobs_api.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend/tests/test_jobs_api.py backend/tests/conftest.py
git commit -m "test: add async job api coverage"
```

### Task 2: Add queue config, worker runner, and jobs API

**Files:**
- Modify: `/opt/Paper/backend/app/config.py`
- Create: `/opt/Paper/backend/app/queue.py`
- Create: `/opt/Paper/backend/app/jobs.py`
- Create: `/opt/Paper/backend/app/services/pipeline_runner.py`
- Create: `/opt/Paper/backend/app/api/routes/jobs.py`
- Modify: `/opt/Paper/backend/app/api/routes/workspace.py`
- Modify: `/opt/Paper/backend/app/main.py`

**Step 1: Write the failing test**

Use the tests from Task 1 as the red state.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/backend && . .venv/bin/activate && pytest tests/test_jobs_api.py -q`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement:
- `PAPER_REDIS_URL`
- queue helper returning an RQ queue
- stage prerequisite validation
- enqueue endpoint returning `202`
- list/get jobs endpoints
- worker processing function that updates `JobRun`

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/backend && . .venv/bin/activate && pytest tests/test_jobs_api.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add backend
git commit -m "feat: add async pipeline job orchestration"
```

### Task 3: Add failing frontend tests for polling and disabled stage controls

**Files:**
- Modify: `/opt/Paper/frontend/src/App.test.tsx`
- Create: `/opt/Paper/frontend/src/components/ExportPanel.test.tsx`

**Step 1: Write the failing test**

Add tests asserting:
- a queued or running stage disables the matching button
- the app polls jobs while work is active
- the app refreshes workspace after jobs finish
- failed jobs show a visible error message

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx src/components/ExportPanel.test.tsx`
Expected: FAIL because jobs polling and failure UI do not exist.

**Step 3: Write minimal implementation**

Only add the UI and API hooks necessary for polling and status display.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx src/components/ExportPanel.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add frontend
git commit -m "feat: add async job polling ui"
```

### Task 4: Wire frontend jobs API and stage-state UX

**Files:**
- Modify: `/opt/Paper/frontend/src/lib/api.ts`
- Modify: `/opt/Paper/frontend/src/lib/types.ts`
- Modify: `/opt/Paper/frontend/src/App.tsx`
- Modify: `/opt/Paper/frontend/src/components/UploadPanel.tsx`
- Modify: `/opt/Paper/frontend/src/components/OutlinePanel.tsx`
- Modify: `/opt/Paper/frontend/src/components/DraftPanel.tsx`
- Modify: `/opt/Paper/frontend/src/components/EvidenceReviewPanel.tsx`
- Modify: `/opt/Paper/frontend/src/components/ExportPanel.tsx`
- Modify: `/opt/Paper/frontend/src/components/ProjectWorkspace.tsx`

**Step 1: Write the failing test**

Use the tests from Task 3 as the red state.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx src/components/ExportPanel.test.tsx`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement:
- jobs list API client
- active-stage polling loop
- stage button disable logic
- failed-job message rendering

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx src/components/ExportPanel.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add frontend
git commit -m "feat: wire async pipeline status polling"
```

### Task 5: Add redis/worker runtime wiring and verify the full stack

**Files:**
- Modify: `/opt/Paper/.env.example`
- Modify: `/opt/Paper/README.md`
- Modify: `/opt/Paper/docker-compose.yml`

**Step 1: Write the failing test**

Use configuration validation and full verification commands as the red state.

**Step 2: Run checks to verify they fail or are incomplete**

Run: `cd /opt/Paper && docker compose config`
Expected: The worker/redis services are missing before implementation.

**Step 3: Write minimal implementation**

Add:
- `PAPER_REDIS_URL`
- `redis` service
- `worker` service
- README notes for worker startup and job architecture

**Step 4: Run full verification**

Run: `cd /opt/Paper/backend && . .venv/bin/activate && pytest -q`
Expected: PASS

Run: `cd /opt/Paper/frontend && npm test -- --run`
Expected: PASS

Run: `cd /opt/Paper/frontend && npm run build`
Expected: PASS

Run: `cd /opt/Paper && docker compose config`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add .
git commit -m "feat: add worker-backed async pipeline runtime"
```
