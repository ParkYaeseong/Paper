from __future__ import annotations

from pathlib import Path

from app.models import Artifact, ArtifactChunk, Project
from app.services.normalization import run_ingest


def test_run_ingest_builds_role_aware_context_and_persists_full_text_chunks(db_session_factory, tmp_path) -> None:
    brief_text = (
        "# Project Intake\n\n"
        "protein_pipeline is a systems paper about workflow orchestration.\n\n"
        + ("intro text " * 80)
        + "\n\n## Distinctive Contributions\n\n"
        "Safe partial reruns and run_id tracking are first-class workflow concepts.\n"
    )
    readme_text = "# README\n\nRuntime notes and endpoint configuration.\n\n" + ("ops text " * 90)
    results_csv = "metric,value\nsuccess_rate,0.82\ncycle_time,14\n"

    brief_path = tmp_path / "project_intake.md"
    brief_path.write_text(brief_text, encoding="utf-8")
    readme_path = tmp_path / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8")
    results_path = tmp_path / "results.csv"
    results_path.write_text(results_csv, encoding="utf-8")

    with db_session_factory() as session:
        project = Project(
            owner_sub="user-1",
            owner_username="tester",
            title="protein_pipeline manuscript",
            objective="Describe the workflow system and its results context.",
        )
        session.add(project)
        session.flush()

        session.add_all(
            [
                Artifact(
                    project_id=project.id,
                    kind="upload",
                    filename="project_intake.md",
                    content_type="text/markdown",
                    storage_path=str(brief_path),
                    size_bytes=brief_path.stat().st_size,
                    sha256="brief",
                    metadata_json={"role": "narrative_brief"},
                ),
                Artifact(
                    project_id=project.id,
                    kind="upload",
                    filename="README.md",
                    content_type="text/markdown",
                    storage_path=str(readme_path),
                    size_bytes=readme_path.stat().st_size,
                    sha256="readme",
                    metadata_json={"role": "supporting_doc"},
                ),
                Artifact(
                    project_id=project.id,
                    kind="upload",
                    filename="results.csv",
                    content_type="text/csv",
                    storage_path=str(results_path),
                    size_bytes=results_path.stat().st_size,
                    sha256="results",
                    metadata_json={"role": "results_table"},
                ),
            ]
        )
        session.commit()

        profile = run_ingest(session, project)

        assert profile.summary_json["project_brief"]["title"] == "protein_pipeline manuscript"
        assert profile.summary_json["dataset_summary"]["artifact_count"] == 3
        assert profile.summary_json["dataset_summary"]["table_count"] == 1
        assert profile.summary_json["dataset_summary"]["source_artifacts"] == [
            {
                "artifact_id": profile.summary_json["dataset_summary"]["source_artifacts"][0]["artifact_id"],
                "filename": "project_intake.md",
                "role": "narrative_brief",
                "sha256": "brief",
            },
            {
                "artifact_id": profile.summary_json["dataset_summary"]["source_artifacts"][1]["artifact_id"],
                "filename": "README.md",
                "role": "supporting_doc",
                "sha256": "readme",
            },
            {
                "artifact_id": profile.summary_json["dataset_summary"]["source_artifacts"][2]["artifact_id"],
                "filename": "results.csv",
                "role": "results_table",
                "sha256": "results",
            },
        ]
        assert profile.summary_json["narrative_context"]["artifact_count"] == 1
        assert profile.summary_json["supporting_context"]["artifact_count"] == 1
        assert profile.summary_json["results_context"]["table_count"] == 1
        assert profile.summary_json["results_context"]["tables"][0]["filename"] == "results.csv"
        assert profile.summary_json["results_context"]["tables"][0]["sample_rows"] == [
            {"metric": "success_rate", "value": "0.82"},
            {"metric": "cycle_time", "value": "14"},
        ]

        chunks = (
            session.query(ArtifactChunk)
            .filter(ArtifactChunk.project_id == project.id)
            .order_by(ArtifactChunk.artifact_id, ArtifactChunk.ordinal)
            .all()
        )
        assert chunks
        roles = {chunk.role for chunk in chunks}
        assert "narrative_brief" in roles
        assert "supporting_doc" in roles
        narrative_text = "\n".join(chunk.content for chunk in chunks if chunk.role == "narrative_brief")
        assert "Safe partial reruns and run_id tracking are first-class workflow concepts." in narrative_text
