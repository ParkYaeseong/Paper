import type {
  AuthConfig,
  JobListResponse,
  ProjectListResponse,
  User,
  Workspace
} from "./types";


async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    ...init,
    headers: {
      ...(init?.headers || {})
    }
  });
  if (response.status === 401) {
    throw new Error("UNAUTHORIZED");
  }
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export function getAuthConfig(): Promise<AuthConfig> {
  return apiFetch<AuthConfig>("/api/auth/oidc/config");
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    const payload = await apiFetch<{ user: User | null }>("/api/auth/me");
    return payload.user;
  } catch (error) {
    if (error instanceof Error && error.message === "UNAUTHORIZED") {
      return null;
    }
    throw error;
  }
}

export function exchangeOidcCode(input: {
  code: string;
  redirect_uri: string;
  code_verifier?: string;
}): Promise<{ ok: boolean; user: User }> {
  return apiFetch("/api/auth/oidc/exchange", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export function logout(): Promise<{ ok: boolean }> {
  return apiFetch("/api/auth/logout", { method: "POST" });
}

export function listProjects(): Promise<ProjectListResponse> {
  return apiFetch<ProjectListResponse>("/api/projects");
}

export function createProject(input: { title: string; objective: string }) {
  return apiFetch("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export function uploadArtifacts(projectId: string, files: File[]) {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  return apiFetch(`/api/projects/${projectId}/artifacts`, {
    method: "POST",
    body: form
  });
}

export async function deleteArtifact(projectId: string, artifactId: string) {
  const response = await fetch(`/api/projects/${projectId}/artifacts/${artifactId}`, {
    method: "DELETE",
    credentials: "include"
  });
  if (response.status === 401) {
    throw new Error("UNAUTHORIZED");
  }
  if (!response.ok) {
    throw new Error(await response.text());
  }
}

export function getWorkspace(projectId: string): Promise<Workspace> {
  return apiFetch<Workspace>(`/api/projects/${projectId}/workspace`);
}

export function listJobs(projectId: string): Promise<JobListResponse> {
  return apiFetch<JobListResponse>(`/api/projects/${projectId}/jobs`);
}

export function runPipelineStage(projectId: string, stage: string) {
  return apiFetch<{ ok: boolean; job: { id: string; stage: string; status: string } }>(
    `/api/projects/${projectId}/pipeline/${stage}`,
    { method: "POST" }
  );
}

export function updateDraftSection(projectId: string, sectionId: string, content: string) {
  return apiFetch(`/api/projects/${projectId}/draft-sections/${sectionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content })
  });
}

export function updateCitationSlot(projectId: string, slotId: string, input: { status: string; selected_reference_ids_json?: string[] }) {
  return apiFetch(`/api/projects/${projectId}/citation-slots/${slotId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}
