from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import CitationSlot, DatasetProfile, Outline, Project
from app.services import llm


def _outline_version(session: Session, project_id: str) -> int:
    version = session.scalar(select(func.max(Outline.version)).where(Outline.project_id == project_id))
    return int(version or 0) + 1


def _fallback_outline(project: Project, profile: DatasetProfile) -> dict[str, object]:
    objective = project.objective or "Describe the uploaded research data and findings."
    table_count = profile.summary_json.get("dataset_summary", {}).get("table_count", 0)
    return {
        "manuscript_type": "original_article",
        "title_candidates": [
            project.title,
            f"{project.title}: evidence-grounded manuscript draft",
        ],
        "sections": [
            {
                "key": "introduction",
                "heading": "Introduction",
                "claims": [
                    "Recent advances in biofoundry automation have improved experimental throughput.",
                    f"Resource allocation may influence performance outcomes in studies like {objective.lower()}",
                ],
            },
            {
                "key": "methods",
                "heading": "Methods",
                "claims": [
                    "Structured project artifacts can be normalized into a manuscript-ready research profile.",
                ],
            },
            {
                "key": "results",
                "heading": "Results",
                "claims": [],
                "notes": [f"The current upload contains {table_count} tabular dataset(s)."],
            },
            {
                "key": "discussion",
                "heading": "Discussion",
                "claims": [
                    "Higher resource input may accelerate DBTL cycle efficiency.",
                    "Grounded review is necessary before turning data summaries into publication claims.",
                ],
            },
            {
                "key": "limitations",
                "heading": "Limitations",
                "claims": [],
            },
            {
                "key": "conclusion",
                "heading": "Conclusion",
                "claims": [],
            },
        ],
    }


def _build_outline(project: Project, profile: DatasetProfile) -> dict[str, object]:
    system_prompt = (
        "You are planning a scientific manuscript. Return JSON with manuscript_type, "
        "title_candidates, and sections. Each section needs key, heading, and claims."
    )
    user_prompt = (
        f"Project title: {project.title}\n"
        f"Objective: {project.objective}\n"
        f"Dataset profile:\n{profile.summary_json}\n"
        "Return a concise manuscript outline with citation-worthy claims in introduction, methods, and discussion."
    )
    llm_result = llm.openai_chat_json(system_prompt, user_prompt)
    if isinstance(llm_result, dict):
        return llm_result
    return _fallback_outline(project, profile)


def run_plan(session: Session, project: Project) -> Outline:
    profile = session.scalars(
        select(DatasetProfile).where(DatasetProfile.project_id == project.id).order_by(DatasetProfile.version.desc())
    ).first()
    if profile is None:
        raise ValueError("dataset profile is required before planning")

    outline_data = _build_outline(project, profile)
    outline = Outline(
        project_id=project.id,
        version=_outline_version(session, project.id),
        manuscript_type=str(outline_data.get("manuscript_type") or "original_article"),
        title_candidates_json=list(outline_data.get("title_candidates") or []),
        outline_json={"sections": outline_data.get("sections") or []},
    )
    session.add(outline)
    session.flush()

    session.execute(delete(CitationSlot).where(CitationSlot.project_id == project.id))
    sections = outline.outline_json.get("sections") or []
    for section in sections:
        section_key = str(section.get("key") or "").strip() or "section"
        for index, claim in enumerate(section.get("claims") or [], start=1):
            slot = CitationSlot(
                project_id=project.id,
                section_key=section_key,
                slot_key=f"CIT_{section_key.upper()}_{index}",
                claim_text=str(claim).strip(),
                context_text=str(section.get("heading") or ""),
                ordinal=index,
                status="pending",
            )
            session.add(slot)

    session.commit()
    session.refresh(outline)
    return outline
