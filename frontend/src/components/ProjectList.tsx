import { useState } from "react";

import type { Project } from "../lib/types";


type ProjectListProps = {
  projects: Project[];
  selectedProjectId: string | null;
  onSelectProject: (projectId: string) => void;
  onCreateProject: (input: { title: string; objective: string }) => Promise<void>;
};


export default function ProjectList({
  projects,
  selectedProjectId,
  onSelectProject,
  onCreateProject
}: ProjectListProps) {
  const [title, setTitle] = useState("");
  const [objective, setObjective] = useState("");
  const [creating, setCreating] = useState(false);

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
        <button className="primary-button" disabled={creating} onClick={handleCreate} type="button">
          Create Project
        </button>
      </div>
    </aside>
  );
}
