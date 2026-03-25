from __future__ import annotations

from app.models import Artifact, DraftSection, Outline, Project
from app.services.drafting import run_draft
from app.services.normalization import run_ingest
from app.services.planning import run_plan


def test_role_aware_ingest_drives_system_paper_outline_and_results_draft(db_session_factory, tmp_path) -> None:
    brief_path = tmp_path / "project_intake_system_paper.md"
    brief_path.write_text(
        (
            "# protein_pipeline System Paper\n\n"
            "This is a system paper about workflow orchestration and interactive analysis.\n\n"
            "## Core Technical Contributions\n\n"
            "- MCP-enabled orchestration layer\n"
            "- safe partial rerun model with run_id tracking\n"
            "- interactive analysis and reporting surfaces\n"
        ),
        encoding="utf-8",
    )
    readme_path = tmp_path / "README.md"
    readme_path.write_text(
        (
            "# README\n\n"
            "- RunPod Admin console\n"
            "- Workflow Studio and Analyze views\n"
        ),
        encoding="utf-8",
    )
    results_path = tmp_path / "results.csv"
    results_path.write_text(
        "metric,value\nsuccess_rate,0.82\ncycle_time,14\n",
        encoding="utf-8",
    )

    with db_session_factory() as session:
        project = Project(
            owner_sub="user-1",
            owner_username="tester",
            title="protein_pipeline manuscript",
            objective="Present protein_pipeline as a reproducible system for workflow orchestration.",
        )
        session.add(project)
        session.flush()

        session.add_all(
            [
                Artifact(
                    project_id=project.id,
                    kind="upload",
                    filename="project_intake_system_paper.md",
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

        run_ingest(session, project)
        outline = run_plan(session, project)
        sections = run_draft(session, project)

        assert isinstance(outline, Outline)
        assert outline.manuscript_type == "system_paper"
        headings = [section["heading"] for section in outline.outline_json["sections"]]
        assert "System Overview" in headings
        assert "Architecture" in headings
        assert "Evaluation" in headings

        draft_map = {section.section_key: section for section in sections}
        assert isinstance(draft_map["introduction"], DraftSection)
        assert "safe partial rerun" in draft_map["introduction"].content.lower()
        assert "MCP-enabled orchestration layer" in draft_map["system_overview"].content
        assert "success_rate" in draft_map["evaluation"].content
        assert "cycle_time" in draft_map["evaluation"].content
