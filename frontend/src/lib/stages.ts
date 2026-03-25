import type { JobRun } from "./types";


type StageMeta = {
  label: string;
  runningLabel: string;
  description: string;
};


const STAGE_META: Record<string, StageMeta> = {
  ingest: {
    label: "Ingest",
    runningLabel: "Ingest Running...",
    description: "Building the project profile from uploaded files.",
  },
  plan: {
    label: "Plan",
    runningLabel: "Plan Running...",
    description: "Generating the manuscript outline and citation slots.",
  },
  draft: {
    label: "Draft",
    runningLabel: "Draft Running...",
    description: "Writing manuscript sections from the structured project profile.",
  },
  retrieve: {
    label: "Retrieve",
    runningLabel: "Retrieve Running...",
    description: "Searching external literature for candidate references.",
  },
  ground: {
    label: "Ground",
    runningLabel: "Ground Running...",
    description: "Scoring candidate references against manuscript claims.",
  },
  evidence: {
    label: "Evidence",
    runningLabel: "Evidence Running...",
    description: "Searching literature and grounding citation slots.",
  },
  export: {
    label: "Export",
    runningLabel: "Export Running...",
    description: "Preparing manuscript files for download.",
  },
};


const STAGE_ALIASES: Record<string, string[]> = {
  evidence: ["evidence", "retrieve", "ground"],
};


export type JobNotice = {
  id: string;
  stage: string;
  status: string;
  logText: string;
};


export function isActiveJob(job: Pick<JobRun, "status">) {
  return job.status === "queued" || job.status === "running";
}


export function sortJobsByRecency(jobs: JobRun[]) {
  return [...jobs].sort((left, right) => {
    const leftTime = Date.parse(left.updated_at || left.created_at || "") || 0;
    const rightTime = Date.parse(right.updated_at || right.created_at || "") || 0;
    return rightTime - leftTime;
  });
}


export function stageLabel(stage: string) {
  return STAGE_META[stage]?.label || stage.charAt(0).toUpperCase() + stage.slice(1);
}


export function stageRunLabel(stage: string) {
  return `Run ${stageLabel(stage)}`;
}


export function stageRunningLabel(stage: string) {
  return STAGE_META[stage]?.runningLabel || `${stageLabel(stage)} Running...`;
}


export function stageDescription(stage: string) {
  return STAGE_META[stage]?.description || "Background processing is in progress.";
}


export function stageIsBusy(stage: string, jobs: JobRun[], pendingStage: string | null) {
  const aliases = STAGE_ALIASES[stage] || [stage];
  if (pendingStage && aliases.includes(pendingStage)) {
    return true;
  }
  return jobs.some((job) => aliases.includes(job.stage) && isActiveJob(job));
}


export function stageStatusTitle(stage: string, status: string) {
  const label = stageLabel(stage);
  if (status === "queued") return `${label} queued`;
  if (status === "running") return `${label} running`;
  if (status === "succeeded") return `${label} succeeded`;
  if (status === "failed") return `${label} failed`;
  return `${label} ${status}`;
}
