import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

vi.mock("./lib/api", () => ({
  createProject: vi.fn(),
  deleteProject: vi.fn(),
  deleteArtifact: vi.fn(),
  exchangeOidcCode: vi.fn(),
  getAuthConfig: vi.fn(),
  getCurrentUser: vi.fn(),
  getWorkspace: vi.fn(),
  listJobs: vi.fn(),
  listProjects: vi.fn(),
  logout: vi.fn(),
  runPipelineStage: vi.fn(),
  updateCitationSlot: vi.fn(),
  updateDraftSection: vi.fn(),
  uploadArtifacts: vi.fn(),
}));

import { deleteProject, getAuthConfig, getCurrentUser, getWorkspace, listJobs, listProjects, runPipelineStage } from "./lib/api";


function buildWorkspace(overrides: Record<string, unknown> = {}) {
  return {
    project: {
      id: "project-1",
      title: "Funding analysis manuscript",
      objective: "Analyze funding and performance outcomes.",
      status: "draft",
      owner_sub: "user-1",
      owner_username: "tester",
      created_at: "2026-03-24T00:00:00Z",
      updated_at: "2026-03-24T00:00:00Z",
    },
    artifacts: [],
    dataset_profile: null,
    outline: null,
    draft_sections: [],
    citation_slots: [],
    reference_records: [],
    evidence_matches: [],
    export_bundle: null,
    jobs: [],
    ...overrides,
  };
}


describe("App", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows a login gate when there is no authenticated user", async () => {
    vi.mocked(getAuthConfig).mockResolvedValue({
      ok: true,
      enabled: true,
      issuer: "https://sso.example.com/realms/kbf",
      client_id: "paper",
      scopes: "openid profile email",
      provider_name: "KBF SSO",
      authorization_endpoint: "https://sso.example.com/auth",
      end_session_endpoint: "https://sso.example.com/logout",
      account_url: "https://sso.example.com/account",
    });
    vi.mocked(getCurrentUser).mockResolvedValue(null);

    render(<App />);

    expect(await screen.findByText("Paper Authoring Studio")).toBeInTheDocument();
    expect(screen.getByText("Sign in with KBF SSO")).toBeInTheDocument();
  });

  it("shows the project workspace shell for an authenticated user", async () => {
    vi.mocked(getAuthConfig).mockResolvedValue({
      ok: true,
      enabled: true,
      issuer: "https://sso.example.com/realms/kbf",
      client_id: "paper",
      scopes: "openid profile email",
      provider_name: "KBF SSO",
      authorization_endpoint: "https://sso.example.com/auth",
      end_session_endpoint: "https://sso.example.com/logout",
      account_url: "https://sso.example.com/account",
    });
    vi.mocked(getCurrentUser).mockResolvedValue({
      sub: "user-1",
      username: "tester",
      email: "tester@example.com",
      name: "Test User",
      role: "user",
    });
    vi.mocked(listProjects).mockResolvedValue({
      items: [
        {
          id: "project-1",
          title: "Funding analysis manuscript",
          objective: "Analyze funding and performance outcomes.",
          status: "draft",
          owner_sub: "user-1",
          owner_username: "tester",
          created_at: "2026-03-24T00:00:00Z",
          updated_at: "2026-03-24T00:00:00Z",
        },
      ],
    });
    vi.mocked(getWorkspace).mockResolvedValue(buildWorkspace());

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 2, name: "Funding analysis manuscript" })).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { level: 2, name: "Create Project" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 3, name: "Workspace" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run Evidence" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Run Retrieve" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Run Ground" })).not.toBeInTheDocument();
  });

  it("polls active jobs and refreshes workspace after completion", async () => {
    vi.mocked(getAuthConfig).mockResolvedValue({
      ok: true,
      enabled: true,
      issuer: "https://sso.example.com/realms/kbf",
      client_id: "paper",
      scopes: "openid profile email",
      provider_name: "KBF SSO",
      authorization_endpoint: "https://sso.example.com/auth",
      end_session_endpoint: "https://sso.example.com/logout",
      account_url: "https://sso.example.com/account",
    });
    vi.mocked(getCurrentUser).mockResolvedValue({
      sub: "user-1",
      username: "tester",
      email: "tester@example.com",
      name: "Test User",
      role: "user",
    });
    vi.mocked(listProjects).mockResolvedValue({
      items: [
        {
          id: "project-1",
          title: "Funding analysis manuscript",
          objective: "Analyze funding and performance outcomes.",
          status: "draft",
          owner_sub: "user-1",
          owner_username: "tester",
          created_at: "2026-03-24T00:00:00Z",
          updated_at: "2026-03-24T00:00:00Z",
        },
      ],
    });
    vi.mocked(getWorkspace).mockResolvedValue(buildWorkspace());

    render(<App />);

    await screen.findByRole("button", { name: "Run Ingest" });
    vi.useFakeTimers();

    vi.mocked(getWorkspace).mockReset();
    vi.mocked(getWorkspace)
      .mockResolvedValueOnce(
        buildWorkspace({
          jobs: [
            {
              id: "job-1",
              stage: "ingest",
              status: "queued",
              payload_json: null,
              result_json: null,
              log_text: "",
              started_at: null,
              finished_at: null,
              created_at: "2026-03-25T00:00:00Z",
              updated_at: "2026-03-25T00:00:00Z",
            },
          ],
        }),
      )
      .mockResolvedValueOnce(buildWorkspace());
    vi.mocked(runPipelineStage).mockResolvedValue({
      ok: true,
      job: { id: "job-1", stage: "ingest", status: "queued" },
    });
    vi.mocked(listJobs)
      .mockResolvedValueOnce({
        items: [
          {
            id: "job-1",
            stage: "ingest",
            status: "running",
            payload_json: null,
            result_json: null,
            log_text: "",
            started_at: "2026-03-25T00:00:01Z",
            finished_at: null,
            created_at: "2026-03-25T00:00:00Z",
            updated_at: "2026-03-25T00:00:01Z",
          },
        ],
      })
      .mockResolvedValueOnce({
        items: [
          {
            id: "job-1",
            stage: "ingest",
            status: "succeeded",
            payload_json: null,
            result_json: { type: "DatasetProfile" },
            log_text: "",
            started_at: "2026-03-25T00:00:01Z",
            finished_at: "2026-03-25T00:00:03Z",
            created_at: "2026-03-25T00:00:00Z",
            updated_at: "2026-03-25T00:00:03Z",
          },
        ],
      });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Run Ingest" }));
    });

    expect(runPipelineStage).toHaveBeenCalledWith("project-1", "ingest");
    expect(screen.getByRole("button", { name: "Ingest Running..." })).toBeDisabled();
    expect(screen.getByText("Ingest queued")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(listJobs).toHaveBeenCalledTimes(1);
    expect(screen.getByText("Ingest running")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(listJobs).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("button", { name: "Run Ingest" })).toBeEnabled();
    expect(screen.getByText("Ingest succeeded")).toBeInTheDocument();
  });

  it("deletes the selected project and clears the workspace when no projects remain", async () => {
    vi.mocked(getAuthConfig).mockResolvedValue({
      ok: true,
      enabled: true,
      issuer: "https://sso.example.com/realms/kbf",
      client_id: "paper",
      scopes: "openid profile email",
      provider_name: "KBF SSO",
      authorization_endpoint: "https://sso.example.com/auth",
      end_session_endpoint: "https://sso.example.com/logout",
      account_url: "https://sso.example.com/account",
    });
    vi.mocked(getCurrentUser).mockResolvedValue({
      sub: "user-1",
      username: "tester",
      email: "tester@example.com",
      name: "Test User",
      role: "user",
    });
    vi.mocked(listProjects)
      .mockResolvedValueOnce({
        items: [
          {
            id: "project-1",
            title: "Funding analysis manuscript",
            objective: "Analyze funding and performance outcomes.",
            status: "draft",
            owner_sub: "user-1",
            owner_username: "tester",
            created_at: "2026-03-24T00:00:00Z",
            updated_at: "2026-03-24T00:00:00Z",
          },
        ],
      })
      .mockResolvedValueOnce({ items: [] });
    vi.mocked(getWorkspace).mockResolvedValue(buildWorkspace());
    vi.mocked(deleteProject).mockResolvedValue(undefined);
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<App />);

    await screen.findByRole("heading", { level: 2, name: "Funding analysis manuscript" });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Delete Selected Project" }));
    });

    expect(deleteProject).toHaveBeenCalledWith("project-1");
    expect(await screen.findByText("Select or create a project")).toBeInTheDocument();
  });

  it("opens the bilingual help guide, switches language, and closes it", async () => {
    vi.mocked(getAuthConfig).mockResolvedValue({
      ok: true,
      enabled: true,
      issuer: "https://sso.example.com/realms/kbf",
      client_id: "paper",
      scopes: "openid profile email",
      provider_name: "KBF SSO",
      authorization_endpoint: "https://sso.example.com/auth",
      end_session_endpoint: "https://sso.example.com/logout",
      account_url: "https://sso.example.com/account",
    });
    vi.mocked(getCurrentUser).mockResolvedValue({
      sub: "user-1",
      username: "tester",
      email: "tester@example.com",
      name: "Test User",
      role: "user",
    });
    vi.mocked(listProjects).mockResolvedValue({
      items: [
        {
          id: "project-1",
          title: "Funding analysis manuscript",
          objective: "Analyze funding and performance outcomes.",
          status: "draft",
          owner_sub: "user-1",
          owner_username: "tester",
          created_at: "2026-03-24T00:00:00Z",
          updated_at: "2026-03-24T00:00:00Z",
        },
      ],
    });
    vi.mocked(getWorkspace).mockResolvedValue(buildWorkspace());

    render(<App />);

    await screen.findByRole("button", { name: "Help / 사용법" });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Help / 사용법" }));
    });

    const dialog = screen.getByRole("dialog", { name: "Usage Guide" });
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByText("Quick Start")).toBeInTheDocument();
    expect(within(dialog).getByText("Upload Selected Files")).toBeInTheDocument();
    expect(within(dialog).getByText("Run Evidence")).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByRole("tab", { name: "한국어" }));
    });

    const koreanDialog = screen.getByRole("dialog", { name: "사용 가이드" });
    expect(koreanDialog).toBeInTheDocument();
    expect(within(koreanDialog).getByText("빠른 시작")).toBeInTheDocument();
    expect(within(koreanDialog).getByText("업로드한 파일이 바뀌면 Run Ingest를 다시 실행하세요.")).toBeInTheDocument();
    expect(within(koreanDialog).getByText("Run Evidence")).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Close guide" }));
    });

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
