import { useEffect, useMemo, useState } from "react";

import GuideModal from "./components/GuideModal";
import Header from "./components/Header";
import JobStatusBar from "./components/JobStatusBar";
import LoginGate from "./components/LoginGate";
import ProjectList from "./components/ProjectList";
import ProjectWorkspace from "./components/ProjectWorkspace";
import {
  createProject,
  deleteProject,
  deleteArtifact,
  exchangeOidcCode,
  getAuthConfig,
  getCurrentUser,
  getWorkspace,
  listJobs,
  listProjects,
  logout,
  runPipelineStage,
  updateCitationSlot,
  updateDraftSection,
  uploadArtifacts
} from "./lib/api";
import { buildOidcAuthorizationUrl, buildOidcRedirectUri, parseOidcCallback, stripOidcCallbackParams } from "./lib/auth";
import type { GuideLanguage } from "./lib/guide-content";
import type { AuthConfig, JobRun, Project, User, Workspace } from "./lib/types";
import { isActiveJob, sortJobsByRecency } from "./lib/stages";


export default function App() {
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [guideLanguage, setGuideLanguage] = useState<GuideLanguage>(() => {
    if (typeof navigator !== "undefined" && navigator.language.toLowerCase().startsWith("ko")) {
      return "ko";
    }
    return "en";
  });
  const [guideOpen, setGuideOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pendingStage, setPendingStage] = useState<string | null>(null);
  const [jobNotice, setJobNotice] = useState<{ id: string; stage: string; status: string; logText: string } | null>(null);

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

  useEffect(() => {
    setPendingStage(null);
    setJobNotice(null);
  }, [selectedProjectId]);

  useEffect(() => {
    if (!selectedProjectId || !user || !workspace) return;
    if (!workspace.jobs.some(isActiveJob)) return;

    const timer = window.setTimeout(async () => {
      try {
        const response = await listJobs(selectedProjectId);
        setWorkspace((current) => (current ? { ...current, jobs: response.items } : current));
        if (!response.items.some(isActiveJob)) {
          const latestJob = sortJobsByRecency(response.items)[0];
          if (latestJob && (latestJob.status === "succeeded" || latestJob.status === "failed")) {
            setJobNotice({
              id: latestJob.id,
              stage: latestJob.stage,
              status: latestJob.status,
              logText: latestJob.log_text,
            });
          }
          await refreshWorkspace(selectedProjectId);
        }
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "Failed to poll jobs.");
      }
    }, 2000);

    return () => {
      window.clearTimeout(timer);
    };
  }, [selectedProjectId, user, workspace]);

  useEffect(() => {
    if (!workspace) return;
    const jobs = sortJobsByRecency(workspace.jobs);
    const activeJob = jobs.find(isActiveJob);

    if (activeJob) {
      setJobNotice({
        id: activeJob.id,
        stage: activeJob.stage,
        status: activeJob.status,
        logText: activeJob.log_text,
      });
      return;
    }

    const latestJob = jobs[0];
    if (!latestJob) {
      return;
    }

    if (latestJob.status === "failed") {
      setJobNotice({
        id: latestJob.id,
        stage: latestJob.stage,
        status: latestJob.status,
        logText: latestJob.log_text,
      });
      return;
    }

    if (latestJob.status === "succeeded") {
      setJobNotice({
        id: latestJob.id,
        stage: latestJob.stage,
        status: latestJob.status,
        logText: latestJob.log_text,
      });
      const timer = window.setTimeout(() => {
        setJobNotice((current) => (current?.id === latestJob.id ? null : current));
      }, 3500);
      return () => {
        window.clearTimeout(timer);
      };
    }
  }, [workspace, pendingStage]);

  useEffect(() => {
    if (!pendingStage) return;
    setJobNotice({
      id: `pending-${pendingStage}`,
      stage: pendingStage,
      status: "queued",
      logText: "",
    });
  }, [pendingStage]);

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

  async function handleDeleteProject(projectId: string) {
    const deletingSelected = selectedProjectId === projectId;
    await deleteProject(projectId);
    const items = await refreshProjects();
    if (!items.length) {
      setSelectedProjectId(null);
      setWorkspace(null);
      return;
    }
    if (deletingSelected) {
      const nextProjectId = items[0].id;
      setSelectedProjectId(nextProjectId);
      await refreshWorkspace(nextProjectId);
      return;
    }
    if (selectedProjectId) {
      await refreshWorkspace(selectedProjectId);
    }
  }

  async function handleUploadFiles(files: File[]) {
    if (!selectedProjectId) return;
    await uploadArtifacts(selectedProjectId, files);
    await refreshWorkspace(selectedProjectId);
  }

  async function handleDeleteArtifact(artifactId: string) {
    if (!selectedProjectId) return;
    await deleteArtifact(selectedProjectId, artifactId);
    await refreshWorkspace(selectedProjectId);
  }

  async function handleRunStage(stage: string) {
    if (!selectedProjectId) return;
    setError(null);
    setPendingStage(stage);
    try {
      await runPipelineStage(selectedProjectId, stage);
      await refreshWorkspace(selectedProjectId);
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Failed to run stage.";
      setError(message);
      setJobNotice({
        id: `failed-${stage}-${Date.now()}`,
        stage,
        status: "failed",
        logText: message,
      });
    } finally {
      setPendingStage(null);
    }
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
      <Header onLogout={handleLogout} onOpenGuide={() => setGuideOpen(true)} user={user} />
      {jobNotice ? <JobStatusBar notice={jobNotice} /> : null}
      <GuideModal
        language={guideLanguage}
        onClose={() => setGuideOpen(false)}
        onLanguageChange={setGuideLanguage}
        open={guideOpen}
      />
      <div className="content-shell">
        <ProjectList
          onCreateProject={handleCreateProject}
          onDeleteProject={handleDeleteProject}
          onSelectProject={setSelectedProjectId}
          projects={projects}
          selectedProjectId={selectedProjectId}
        />
        {selectedProject && workspace ? (
          <ProjectWorkspace
            onDeleteArtifact={handleDeleteArtifact}
            pendingStage={pendingStage}
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
