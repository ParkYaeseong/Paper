import { useEffect, useMemo, useState } from "react";

import Header from "./components/Header";
import LoginGate from "./components/LoginGate";
import ProjectList from "./components/ProjectList";
import ProjectWorkspace from "./components/ProjectWorkspace";
import {
  createProject,
  exchangeOidcCode,
  getAuthConfig,
  getCurrentUser,
  getWorkspace,
  listProjects,
  logout,
  runPipelineStage,
  updateCitationSlot,
  updateDraftSection,
  uploadArtifacts
} from "./lib/api";
import { buildOidcAuthorizationUrl, buildOidcRedirectUri, parseOidcCallback, stripOidcCallbackParams } from "./lib/auth";
import type { AuthConfig, Project, User, Workspace } from "./lib/types";


export default function App() {
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshProjects() {
    const response = await listProjects();
    setProjects(response.items);
    if (!selectedProjectId && response.items.length) {
      setSelectedProjectId(response.items[0].id);
    }
    return response.items;
  }

  async function refreshWorkspace(projectId: string) {
    const nextWorkspace = await getWorkspace(projectId);
    setWorkspace(nextWorkspace);
  }

  useEffect(() => {
    let mounted = true;
    async function bootstrap() {
      setLoading(true);
      try {
        const config = await getAuthConfig();
        if (!mounted) return;
        setAuthConfig(config);
        const callback = parseOidcCallback();
        if (callback.code) {
          await exchangeOidcCode({ code: callback.code, redirect_uri: buildOidcRedirectUri() });
          window.history.replaceState({}, document.title, stripOidcCallbackParams(window.location.href));
        }
        const currentUser = await getCurrentUser();
        if (!mounted) return;
        setUser(currentUser);
        if (currentUser) {
          const loadedProjects = await refreshProjects();
          if (loadedProjects.length) {
            await refreshWorkspace(loadedProjects[0].id);
          }
        }
      } catch (caughtError) {
        if (!mounted) return;
        setError(caughtError instanceof Error ? caughtError.message : "Failed to load application state.");
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    void bootstrap();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedProjectId || !user) return;
    void refreshWorkspace(selectedProjectId);
  }, [selectedProjectId, user]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );

  async function handleLogin() {
    if (!authConfig?.authorization_endpoint || !authConfig.client_id) return;
    const url = buildOidcAuthorizationUrl({
      authorizationEndpoint: authConfig.authorization_endpoint,
      clientId: authConfig.client_id,
      redirectUri: buildOidcRedirectUri(),
      scopes: authConfig.scopes || "openid profile email",
      state: crypto.randomUUID()
    });
    window.location.assign(url);
  }

  async function handleLogout() {
    await logout();
    setUser(null);
    setProjects([]);
    setSelectedProjectId(null);
    setWorkspace(null);
  }

  async function handleCreateProject(input: { title: string; objective: string }) {
    const project = await createProject(input) as Project;
    const items = await refreshProjects();
    const target = items.find((candidate) => candidate.id === project.id) ?? project;
    setSelectedProjectId(target.id);
    await refreshWorkspace(target.id);
  }

  async function handleUploadFiles(files: File[]) {
    if (!selectedProjectId) return;
    await uploadArtifacts(selectedProjectId, files);
    await refreshWorkspace(selectedProjectId);
  }

  async function handleRunStage(stage: string) {
    if (!selectedProjectId) return;
    await runPipelineStage(selectedProjectId, stage);
    await refreshWorkspace(selectedProjectId);
  }

  async function handleSaveSection(sectionId: string, content: string) {
    if (!selectedProjectId) return;
    await updateDraftSection(selectedProjectId, sectionId, content);
    await refreshWorkspace(selectedProjectId);
  }

  async function handleReviewSlot(slotId: string, status: string, selectedReferenceIds?: string[]) {
    if (!selectedProjectId) return;
    await updateCitationSlot(selectedProjectId, slotId, {
      status,
      selected_reference_ids_json: selectedReferenceIds
    });
    await refreshWorkspace(selectedProjectId);
  }

  if (loading) {
    return <div className="loading-shell">Loading Paper Authoring Studio...</div>;
  }

  if (!user) {
    return <LoginGate authConfig={authConfig} error={error} onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <Header onLogout={handleLogout} user={user} />
      <div className="content-shell">
        <ProjectList
          onCreateProject={handleCreateProject}
          onSelectProject={setSelectedProjectId}
          projects={projects}
          selectedProjectId={selectedProjectId}
        />
        {selectedProject && workspace ? (
          <ProjectWorkspace
            onReviewSlot={handleReviewSlot}
            onRunStage={handleRunStage}
            onSaveSection={handleSaveSection}
            onUploadFiles={handleUploadFiles}
            workspace={workspace}
          />
        ) : (
          <main className="workspace empty-state">
            <div className="hero-card compact">
              <p className="eyebrow">Workspace</p>
              <h2>Select or create a project</h2>
              <p>Projects hold uploads, manuscript state, evidence matches, and export bundles.</p>
            </div>
          </main>
        )}
      </div>
    </div>
  );
}
