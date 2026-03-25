from __future__ import annotations

from app.config import get_settings
from app.models import DraftSection, FigureAsset, FigureSpec, Project
from app.services.figures import run_generate_figures


def test_run_generate_figures_creates_prepared_handoff_specs(db_session_factory) -> None:
    with db_session_factory() as session:
        project = Project(
            owner_sub="user-1",
            owner_username="tester",
            title="protein_pipeline manuscript",
            objective="Summarize the interactive protein design workflow.",
        )
        session.add(project)
        session.flush()

        session.add(
            DraftSection(
                project_id=project.id,
                section_key="methods",
                heading="Methods",
                version=1,
                content=(
                    "The workflow combines setup, staged execution, and review.\n\n"
                    "[FIGURE_1: Overall protein_pipeline architecture and UI flow.]"
                ),
                status="drafted",
            )
        )
        session.commit()

        specs = run_generate_figures(session, project, get_settings())

        assert len(specs) == 1
        spec = specs[0]
        assert isinstance(spec, FigureSpec)
        assert spec.figure_key == "FIGURE_1"
        assert spec.status == "prepared"
        assert spec.caption_draft == "Overall protein_pipeline architecture and UI flow."
        assert "[FIGURE_1:" not in spec.method_section_content
        assert "### Methods" in spec.method_section_content
        assert "The workflow combines setup, staged execution, and review." in spec.method_section_content

        stored_specs = session.query(FigureSpec).filter(FigureSpec.project_id == project.id).all()
        stored_assets = session.query(FigureAsset).filter(FigureAsset.project_id == project.id).all()
        assert len(stored_specs) == 1
        assert stored_assets == []
