import { useState } from "react";

import type { Project } from "../lib/types";


type ProjectListProps = {
  projects: Project[];
  selectedProjectId: string | null;
  onSelectProject: (projectId: string) => void;
  onCreateProject: (input: { title: string; objective: string }) => Promise<void>;
  onDeleteProject: (projectId: string) => Promise<void>;
};


export default function ProjectList({
  projects,
  selectedProjectId,
  onSelectProject,
  onCreateProject,
  onDeleteProject
}: ProjectListProps) {
  const [title, setTitle] = useState("");
  const [objective, setObjective] = useState("");
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? null;

  async function handleCreate() {
    if (!title.trim()) return;
    setCreating(true);
    try {
      await onCreateProject({ title: title.trim(), objective: objective.trim() });
      setTitle("");
      setObjective("");
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteSelectedProject() {
    if (!selectedProject) return;
    if (!window.confirm(`Delete project "${selectedProject.title}"? This removes uploads, drafts, citations, and exports.`)) {
      return;
    }
    setDeleting(true);
    try {
      await onDeleteProject(selectedProject.id);
    } finally {
      setDeleting(false);
    }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <div className="sidebar-header-row">
          <h2>Projects</h2>
          <span className="count-badge">{projects.length}</span>
        </div>
        <div className="project-list">
          {projects.map((project) => (
            <button
              className={project.id === selectedProjectId ? "project-card selected" : "project-card"}
              key={project.id}
              onClick={() => onSelectProject(project.id)}
              type="button"
            >
              <strong>{project.title}</strong>
              <span>{project.objective || "No objective yet"}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-header-row">
          <h2>Create Project</h2>
        </div>
        <label className="field">
          <span>Title</span>
          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Funding analysis manuscript" />
        </label>
        <label className="field">
          <span>Objective</span>
          <textarea value={objective} onChange={(event) => setObjective(event.target.value)} placeholder="Relate funding levels to throughput and yield." />
        </label>
        <div className="button-row">
          <button className="primary-button" disabled={creating || deleting} onClick={handleCreate} type="button">
            Create Project
          </button>
          {selectedProject ? (
            <button className="danger-button" disabled={creating || deleting} onClick={handleDeleteSelectedProject} type="button">
              Delete Selected Project
            </button>
          ) : null}
        </div>
      </div>
    </aside>
  );
}
