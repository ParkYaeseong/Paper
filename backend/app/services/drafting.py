from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CitationSlot, DatasetProfile, DraftSection, Outline, Project
from app.services import llm


def _section_version(session: Session, project_id: str, section_key: str) -> int:
    version = session.scalar(
        select(func.max(DraftSection.version)).where(
            DraftSection.project_id == project_id,
            DraftSection.section_key == section_key,
        )
    )
    return int(version or 0) + 1


def _fallback_section_content(
    project: Project,
    profile: DatasetProfile,
    section_key: str,
    heading: str,
    slot_keys: list[str],
) -> str:
    dataset_summary = profile.summary_json.get("dataset_summary", {})
    table_count = dataset_summary.get("table_count", 0)
    if section_key == "introduction":
        lines = [
            f"{project.title} addresses the question: {project.objective or 'How internal research data can be turned into a publishable manuscript.'}",
        ]
        for slot_key in slot_keys:
            lines.append(f"This background claim requires literature support [{slot_key}].")
        return "\n\n".join(lines)
    if section_key == "methods":
        lines = [
            f"We normalized {dataset_summary.get('artifact_count', 0)} uploaded artifact(s), including {table_count} tabular dataset(s), into a structured project profile.",
        ]
        for slot_key in slot_keys:
            lines.append(f"Similar data normalization and manuscript preparation approaches have precedent in the literature [{slot_key}].")
        return "\n\n".join(lines)
    if section_key == "results":
        return (
            f"The uploaded project currently contains {table_count} structured table(s). "
            "These normalized inputs are used to draft results narratives and track citation slots."
        )
    if section_key == "discussion":
        lines = [
            "The current draft remains a machine-generated interpretation layer and should be reviewed before submission.",
        ]
        for slot_key in slot_keys:
            lines.append(f"This discussion point is mapped to external evidence [{slot_key}].")
        return "\n\n".join(lines)
    if section_key == "limitations":
        return "This draft uses automated summarization and evidence matching, so domain-expert review remains mandatory."
    return "The project now has a structured manuscript section ready for review."


def run_draft(session: Session, project: Project) -> list[DraftSection]:
    profile = session.scalars(
        select(DatasetProfile).where(DatasetProfile.project_id == project.id).order_by(DatasetProfile.version.desc())
    ).first()
    outline = session.scalars(select(Outline).where(Outline.project_id == project.id).order_by(Outline.version.desc())).first()
    if profile is None or outline is None:
        raise ValueError("dataset profile and outline are required before drafting")

    slots = list(session.scalars(select(CitationSlot).where(CitationSlot.project_id == project.id).order_by(CitationSlot.section_key, CitationSlot.ordinal)))
    slot_map: dict[str, list[str]] = defaultdict(list)
    for slot in slots:
        slot_map[slot.section_key].append(slot.slot_key)

    sections_payload = outline.outline_json.get("sections") or []
    created_sections: list[DraftSection] = []
    for section in sections_payload:
        section_key = str(section.get("key") or "").strip()
        heading = str(section.get("heading") or section_key.title())
        prompt = (
            f"Project: {project.title}\n"
            f"Objective: {project.objective}\n"
            f"Dataset profile: {profile.summary_json}\n"
            f"Section: {heading}\n"
            f"Citation placeholders: {slot_map.get(section_key, [])}\n"
            "Write one concise section using the placeholders exactly."
        )
        content = llm.openai_chat_text(
            "Write concise scientific manuscript sections and preserve citation placeholders exactly.",
            prompt,
        )
        if not content:
            content = _fallback_section_content(project, profile, section_key, heading, slot_map.get(section_key, []))
        draft = DraftSection(
            project_id=project.id,
            section_key=section_key,
            heading=heading,
            version=_section_version(session, project.id, section_key),
            content=content.strip(),
            status="drafted",
        )
        session.add(draft)
        created_sections.append(draft)

    session.commit()
    for draft in created_sections:
        session.refresh(draft)
    return created_sections
