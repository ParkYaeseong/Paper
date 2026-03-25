from __future__ import annotations

from base64 import b64decode
from pathlib import Path

from app.config import get_settings
from app.models import DraftSection, FigureAsset, FigureSpec, Project
from app.services.figures import run_generate_figures


PNG_1X1 = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9VE3D8sAAAAASUVORK5CYII="
)


def test_run_generate_figures_creates_specs_and_assets(db_session_factory, tmp_path, monkeypatch) -> None:
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

        generated = tmp_path / "figure_0.png"
        generated.write_bytes(PNG_1X1)

        monkeypatch.setattr(
            "app.services.figures.generate_paperbanana_candidates",
            lambda **_: [generated],
        )

        specs = run_generate_figures(session, project, get_settings())

        assert len(specs) == 1
        spec = specs[0]
        assert isinstance(spec, FigureSpec)
        assert spec.figure_key == "FIGURE_1"
        assert spec.status == "generated"

        stored_specs = session.query(FigureSpec).filter(FigureSpec.project_id == project.id).all()
        stored_assets = session.query(FigureAsset).filter(FigureAsset.project_id == project.id).all()
        assert len(stored_specs) == 1
        assert len(stored_assets) == 1
        assert stored_assets[0].selected is True
        assert Path(stored_assets[0].artifact.storage_path).exists()

