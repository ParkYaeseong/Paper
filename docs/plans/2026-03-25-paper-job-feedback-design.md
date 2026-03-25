# Paper Job Feedback UX Design

## Goal

Reduce uncertainty when users run pipeline stages by making execution state obvious and by collapsing the two-step evidence workflow into a single action.

## Context

The current UI spreads job feedback across per-panel disabled buttons and a small job strip at the bottom of the export panel. That makes it easy to miss whether a click actually started work. Evidence generation is also exposed as two separate actions, `Run Retrieve` and `Run Ground`, even though users think of it as one workflow step.

## Approach Options

### Option 1: Keep the current backend stages and chain `retrieve -> ground` in the frontend

- Pros: no backend changes
- Cons: fragile across refreshes, duplicates orchestration logic in the browser, and makes job history harder to interpret

### Option 2: Add a backend `evidence` stage and use one frontend action

- Pros: the workflow is represented as one user-facing job, the UI stays simple, and polling logic remains centralized
- Pros: button states and job notifications can use one stage name instead of coordinating two
- Cons: requires a small backend change

### Option 3: Use a blocking modal for all running jobs

- Pros: hard to miss
- Cons: interrupts reading/editing flow and is too heavy for background jobs

## Recommendation

Use **Option 2** and pair it with **non-blocking global feedback**:

- Replace `Run Retrieve` and `Run Ground` with a single `Run Evidence` action.
- Introduce a backend `evidence` stage that sequentially runs retrieval and grounding.
- Change stage buttons so active stages immediately show `Running...`.
- Add a global floating status bar near the header that shows the current active job and brief terminal feedback (`Succeeded`, `Failed`).
- Remove the low-signal job strip from the export panel so status is not split between two places.

## UI Behavior

- When the user clicks a stage button, that button changes immediately to `Running...` and is disabled.
- If a job is active, a floating status bar is shown globally. It includes:
  - Stage label
  - Status label (`Queued`, `Running`, `Succeeded`, `Failed`)
  - Short supporting copy
- When a job completes successfully, the floating bar remains briefly, then auto-dismisses.
- When a job fails, the floating bar stays visible and shows the latest error text if available.
- Evidence review now has a single `Run Evidence` button.

## Data / API Changes

- Add `evidence` to the allowed pipeline stages.
- `ensure_stage_prerequisites()` should require citation slots to exist before `evidence`.
- `run_pipeline_stage()` should run `run_retrieve()` and then `run_grounding()` for `evidence`.
- Jobs API continues to return normal `JobRun` records; the UI treats `evidence` like any other stage.

## Testing

- Backend:
  - `evidence` stage can be enqueued and completes retrieval + grounding in one job.
- Frontend:
  - `Run Evidence` appears instead of `Run Retrieve` / `Run Ground`
  - active buttons show `Running...`
  - global floating status bar appears for active jobs
  - success/failure notifications are shown from polled job transitions

