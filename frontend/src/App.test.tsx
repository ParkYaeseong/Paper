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
  runPipelineStageWithInput: vi.fn(),
  updateFigureSpec: vi.fn(),
  updateArtifactRole: vi.fn(),
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
    quality_report: null,
    figure_specs: [],
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
    expect(screen.getByRole("button", { name: "Run All" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Advanced" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 3, name: "Quality Summary" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 3, name: "Figure Review" })).toBeInTheDocument();
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

    await screen.findByRole("button", { name: "Run All" });
    vi.useFakeTimers();

    vi.mocked(getWorkspace).mockReset();
    vi.mocked(getWorkspace)
      .mockResolvedValueOnce(
        buildWorkspace({
          jobs: [
            {
              id: "job-1",
              stage: "run_all",
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
      .mockResolvedValueOnce(
        buildWorkspace({
          jobs: [
            {
              id: "job-1",
              stage: "run_all",
              status: "running",
              payload_json: null,
              result_json: null,
              log_text: "Running draft",
              started_at: "2026-03-25T00:00:01Z",
              finished_at: null,
              created_at: "2026-03-25T00:00:00Z",
              updated_at: "2026-03-25T00:00:01Z",
            },
          ],
        }),
      )
      .mockResolvedValueOnce(buildWorkspace())
      .mockResolvedValue(buildWorkspace());
    vi.mocked(runPipelineStage).mockResolvedValue({
      ok: true,
      job: { id: "job-1", stage: "run_all", status: "queued" },
    });
    vi.mocked(listJobs)
      .mockResolvedValueOnce({
        items: [
          {
            id: "job-1",
            stage: "run_all",
            status: "running",
            payload_json: null,
            result_json: null,
            log_text: "Running draft",
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
            stage: "run_all",
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
      fireEvent.click(screen.getByRole("button", { name: "Run All" }));
    });

    expect(runPipelineStage).toHaveBeenCalledWith("project-1", "run_all");
    expect(screen.getByRole("button", { name: "Run All Running..." })).toBeDisabled();
    expect(screen.getByText("Run All queued")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(listJobs).toHaveBeenCalledTimes(1);
    expect(screen.getByText("Running Draft")).toBeInTheDocument();
    expect(screen.getByText("Writing manuscript sections from the structured project profile.")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(listJobs).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("button", { name: "Run All" })).toBeEnabled();
    expect(screen.getByText("Run All succeeded")).toBeInTheDocument();
  });

  it("refreshes workspace during an active Run All job so intermediate outputs appear", async () => {
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

    await screen.findByRole("button", { name: "Run All" });
    vi.useFakeTimers();

    vi.mocked(getWorkspace).mockReset();
    vi.mocked(getWorkspace)
      .mockResolvedValueOnce(
        buildWorkspace({
          jobs: [
            {
              id: "job-2",
              stage: "run_all",
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
      .mockResolvedValueOnce(
        buildWorkspace({
          jobs: [
            {
              id: "job-2",
              stage: "run_all",
              status: "running",
              payload_json: null,
              result_json: null,
              log_text: "Running figures",
              started_at: "2026-03-25T00:00:01Z",
              finished_at: null,
              created_at: "2026-03-25T00:00:00Z",
              updated_at: "2026-03-25T00:00:02Z",
            },
          ],
          outline: {
            id: "outline-1",
            version: 1,
            manuscript_type: "original_article",
            title_candidates_json: ["Protein workflow system paper"],
            outline_json: {
              sections: [{ key: "introduction", heading: "Introduction", claims: ["Claim 1"] }],
            },
          },
        }),
      )
      .mockResolvedValue(
        buildWorkspace({
          jobs: [
            {
              id: "job-2",
              stage: "run_all",
              status: "running",
              payload_json: null,
              result_json: null,
              log_text: "Running figures",
              started_at: "2026-03-25T00:00:01Z",
              finished_at: null,
              created_at: "2026-03-25T00:00:00Z",
              updated_at: "2026-03-25T00:00:02Z",
            },
          ],
          outline: {
            id: "outline-1",
            version: 1,
            manuscript_type: "original_article",
            title_candidates_json: ["Protein workflow system paper"],
            outline_json: {
              sections: [{ key: "introduction", heading: "Introduction", claims: ["Claim 1"] }],
            },
          },
        }),
      );
    vi.mocked(runPipelineStage).mockResolvedValue({
      ok: true,
      job: { id: "job-2", stage: "run_all", status: "queued" },
    });
    vi.mocked(listJobs).mockResolvedValueOnce({
      items: [
        {
          id: "job-2",
          stage: "run_all",
          status: "running",
          payload_json: null,
          result_json: null,
          log_text: "Running figures",
          started_at: "2026-03-25T00:00:01Z",
          finished_at: null,
          created_at: "2026-03-25T00:00:00Z",
          updated_at: "2026-03-25T00:00:02Z",
        },
      ],
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Run All" }));
    });

    expect(screen.getByText("No outline yet. Run the planning stage after ingest.")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(listJobs).toHaveBeenCalledTimes(1);
    expect(screen.getByText("original_article")).toBeInTheDocument();
    expect(screen.getByText("Introduction")).toBeInTheDocument();
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
    expect(within(dialog).getByText("Run All")).toBeInTheDocument();
    expect(within(dialog).getByText("Final Export")).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByRole("tab", { name: "한국어" }));
    });

    const koreanDialog = screen.getByRole("dialog", { name: "사용 가이드" });
    expect(koreanDialog).toBeInTheDocument();
    expect(within(koreanDialog).getByText("빠른 시작")).toBeInTheDocument();
    expect(within(koreanDialog).getByText("업로드한 파일이 바뀌면 Run Ingest를 다시 실행하세요.")).toBeInTheDocument();
    expect(within(koreanDialog).getByText("Run All")).toBeInTheDocument();
    expect(within(koreanDialog).getByText("Final Export")).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Close guide" }));
    });

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
