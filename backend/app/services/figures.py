from __future__ import annotations

import re

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Artifact, DraftSection, FigureSpec, Project
from app.services.storage import delete_stored_file


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


def _clean_section_content(content: str) -> str:
    cleaned = FIGURE_PLACEHOLDER_RE.sub("", content)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _build_method_section_content(section: DraftSection, project: Project, caption_draft: str) -> str:
    cleaned = _clean_section_content(section.content)
    if not cleaned:
        cleaned = project.objective.strip() or caption_draft.strip()
    parts = [f"### {section.heading}"]
    if cleaned:
        parts.append(cleaned)
    return "\n\n".join(part for part in parts if part).strip()


def _build_spec(section: DraftSection, figure_number: int, caption_draft: str, project: Project) -> FigureSpec:
    figure_key = f"FIGURE_{figure_number}"
    source_excerpt = _clean_section_content(section.content)
    method_section_content = _build_method_section_content(section, project, caption_draft)
    return FigureSpec(
        project_id=project.id,
        section_key=section.section_key,
        figure_key=figure_key,
        figure_number=figure_number,
        caption_draft=caption_draft.strip(),
        source_excerpt=source_excerpt,
        visual_intent=method_section_content,
        status="prepared",
    )


def run_generate_figures(session: Session, project: Project, settings: Settings) -> list[FigureSpec]:
    del settings
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
            specs.append(spec)

    session.commit()
    for spec in specs:
        session.refresh(spec)
    return specs
