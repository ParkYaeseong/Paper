import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

vi.mock("./lib/api", () => ({
  getAuthConfig: vi.fn(),
  getCurrentUser: vi.fn(),
  listProjects: vi.fn(),
  getWorkspace: vi.fn(),
}));

import { getAuthConfig, getCurrentUser, getWorkspace, listProjects } from "./lib/api";


describe("App", () => {
  beforeEach(() => {
    vi.resetAllMocks();
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
    vi.mocked(getWorkspace).mockResolvedValue({
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
      dataset_profile: null,
      outline: null,
      draft_sections: [],
      citation_slots: [],
      reference_records: [],
      evidence_matches: [],
      export_bundle: null,
      jobs: [],
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 2, name: "Funding analysis manuscript" })).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { level: 2, name: "Create Project" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 3, name: "Workspace" })).toBeInTheDocument();
  });
});
