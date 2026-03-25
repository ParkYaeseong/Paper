# Paper Async Job Orchestration Design

## Goal

Replace synchronous pipeline execution with Redis/RQ-backed asynchronous jobs so the paper authoring UI can enqueue long-running stages, poll status, and refresh results without blocking the request cycle.

## Current Gap

The current API executes `ingest`, `plan`, `draft`, `retrieve`, `ground`, and `export` inline inside the request handler. This makes the UI wait on network-heavy stages, hides intermediate states, and prevents a separate worker process from owning retries and failure isolation.

## Recommended Approach

Use a single Redis queue and a single RQ worker process for v1. Keep `JobRun` as the system-of-record for user-visible state. Let the API enqueue work and return immediately, and let the worker mutate `JobRun` through `queued -> running -> succeeded|failed`.

### Why this approach

- It matches the existing `JobRun` model instead of replacing it.
- It fits the current Docker deployment with minimal surface area.
- It gives clear polling semantics without introducing Celery-level complexity.

## Architecture

```text
frontend
  -> POST /api/projects/{id}/pipeline/{stage}
  -> GET /api/projects/{id}/jobs
backend api
  -> create JobRun(status=queued)
  -> enqueue RQ job(id=job_run.id)
redis
  -> queue storage
worker
  -> load JobRun + Project
  -> run stage service
  -> update JobRun status/result/logs
postgres
  -> canonical manuscript state + JobRun records
```

## Backend Design

### Queue layer

- Add `PAPER_REDIS_URL` config.
- Add `app/queue.py` to build Redis and RQ queue handles.
- Use the database `JobRun.id` as the RQ job id to avoid a second identifier.

### Pipeline runner

- Add `app/services/pipeline_runner.py`.
- Move stage dispatch and prerequisite validation into this module.
- Add a worker entrypoint in `app/jobs.py` that can:
  - process one job by id
  - run the long-lived worker loop

### API behavior

- `POST /api/projects/{project_id}/pipeline/{stage}`
  - validates stage prerequisites
  - rejects duplicate active jobs for the same `project_id + stage`
  - creates `JobRun(status=queued)`
  - enqueues the worker task
  - returns `202 Accepted`
- Add:
  - `GET /api/projects/{project_id}/jobs`
  - `GET /api/projects/{project_id}/jobs/{job_id}`

### Stage prerequisites

- `ingest`: always allowed
- `plan`: requires latest `DatasetProfile`
- `draft`: requires latest `DatasetProfile` and `Outline`
- `retrieve`: requires at least one `CitationSlot`
- `ground`: requires at least one `EvidenceMatch`
- `export`: requires at least one `DraftSection`

## Frontend Design

### Polling flow

- After enqueueing a stage, the SPA immediately refreshes workspace once.
- If any job is `queued` or `running`, the SPA polls `GET /jobs` every 2 seconds.
- When active jobs disappear, the SPA refreshes workspace again to pull new draft/evidence/export state.

### UI changes

- Disable only the button for the currently active stage.
- Keep other stage buttons usable.
- Keep the existing job strip but make queued/running/failed states visible.
- Show the latest failed job message in the export/status area.

## Failure Handling

- Worker exceptions mark the job `failed` and store the message in `log_text`.
- Duplicate active stage requests return `409`.
- Missing prerequisites return `400`.
- Worker code is responsible for setting `started_at` and `finished_at`.

## Deployment Changes

- Add `redis` and `worker` services to `docker-compose.yml`.
- Pass the same `.env` settings to backend and worker.
- Worker command will run `python -m app.jobs`.

## Testing Strategy

### Backend

- enqueue returns `202` and a queued job
- duplicate active jobs are rejected
- jobs can be listed and fetched individually
- direct worker execution updates `JobRun` to `succeeded`
- direct worker execution records `failed` on exception

### Frontend

- queued/running jobs disable the corresponding stage button
- polling refreshes jobs and then workspace on completion
- failed jobs show an error message in the UI

## Out of Scope

- multi-queue prioritization
- distributed scheduling
- automatic stage chaining
- job cancellation
