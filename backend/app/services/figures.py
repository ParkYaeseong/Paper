from __future__ import annotations

from pathlib import Path
import re

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Artifact, DraftSection, FigureAsset, FigureSpec, Project
from app.services.paperbanana_adapter import generate_paperbanana_candidates
from app.services.storage import delete_stored_file, save_generated_file


FIGURE_PLACEHOLDER_RE = re.compile(r"\[FIGURE[_ ](\d+):\s*([^\]]+?)\]")


def _latest_sections(session: Session, project_id: str) -> list[DraftSection]:
    sections = list(
        session.scalars(
            select(DraftSection).where(DraftSection.project_id == project_id).order_by(DraftSection.created_at)
        ).all()
    )
    latest: dict[str, DraftSection] = {}
    for section in sections:
        current = latest.get(section.section_key)
        if current is None or section.version > current.version:
            latest[section.section_key] = section
    return list(latest.values())


def _cleanup_existing_figures(session: Session, project_id: str) -> None:
    figure_artifacts = list(
        session.scalars(
            select(Artifact).where(Artifact.project_id == project_id, Artifact.kind == "figure_candidate")
        ).all()
    )
    for artifact in figure_artifacts:
        delete_stored_file(artifact.storage_path)
        session.delete(artifact)
    session.execute(delete(FigureSpec).where(FigureSpec.project_id == project_id))
    session.flush()


def _build_spec(section: DraftSection, figure_number: int, caption_draft: str, project: Project) -> FigureSpec:
    figure_key = f"FIGURE_{figure_number}"
    source_excerpt = FIGURE_PLACEHOLDER_RE.sub("", section.content).strip()
    visual_intent = f"{project.objective}\n\nSection: {section.heading}\n\nCaption: {caption_draft}".strip()
    return FigureSpec(
        project_id=project.id,
        section_key=section.section_key,
        figure_key=figure_key,
        figure_number=figure_number,
        caption_draft=caption_draft.strip(),
        source_excerpt=source_excerpt,
        visual_intent=visual_intent,
        status="pending",
    )


def run_generate_figures(session: Session, project: Project, settings: Settings) -> list[FigureSpec]:
    sections = _latest_sections(session, project.id)
    if not sections:
        return []

    _cleanup_existing_figures(session, project.id)

    specs: list[FigureSpec] = []
    seen_keys: set[str] = set()
    for section in sections:
        for match in FIGURE_PLACEHOLDER_RE.finditer(section.content):
            figure_number = int(match.group(1))
            figure_key = f"FIGURE_{figure_number}"
            if figure_key in seen_keys:
                continue
            seen_keys.add(figure_key)
            spec = _build_spec(section, figure_number, match.group(2), project)
            session.add(spec)
            session.flush()

            output_dir = Path(settings.storage_root).expanduser().resolve() / "tmp" / project.id / figure_key
            generated_paths = generate_paperbanana_candidates(
                settings=settings,
                content=spec.source_excerpt or spec.visual_intent,
                caption=spec.caption_draft,
                output_dir=output_dir,
            )
            for index, generated_path in enumerate(generated_paths, start=1):
                stored = save_generated_file(
                    settings,
                    project.id,
                    generated_path,
                    subdir=f"figures/{figure_key.lower()}",
                    filename=f"{figure_key.lower()}_{index}.png",
                )
                artifact = Artifact(
                    project_id=project.id,
                    kind="figure_candidate",
                    filename=str(stored["filename"]),
                    content_type=str(stored["content_type"]),
                    storage_path=str(stored["storage_path"]),
                    size_bytes=int(stored["size_bytes"]),
                    sha256=str(stored["sha256"]),
                )
                session.add(artifact)
                session.flush()
                session.add(
                    FigureAsset(
                        project_id=project.id,
                        figure_spec_id=spec.id,
                        artifact_id=artifact.id,
                        provider="paperbanana",
                        status="generated",
                        selected=index == 1,
                    )
                )
            spec.status = "generated"
            session.add(spec)
            specs.append(spec)

    session.commit()
    for spec in specs:
        session.refresh(spec)
    return specs
