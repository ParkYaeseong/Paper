from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ArtifactChunk, DatasetProfile, Project


SYSTEM_PAPER_HINTS = (
    "system paper",
    "platform paper",
    "systems contribution",
    "workflow orchestration",
    "interactive analysis",
    "reproducible research software",
    "web-based console",
    "run_id",
    "safe partial rerun",
    "artifact management",
    "mcp-enabled",
)


def _join_chunks(chunks: list[ArtifactChunk], *, max_chars: int = 7000) -> str:
    parts: list[str] = []
    total = 0
    for chunk in chunks:
        piece = f"{chunk.heading}\n{chunk.content}".strip() if chunk.heading else chunk.content.strip()
        if not piece:
            continue
        if parts and total + len(piece) + 2 > max_chars:
            break
        if not parts and len(piece) > max_chars:
            return piece[:max_chars]
        parts.append(piece)
        total += len(piece) + 2
    return "\n\n".join(parts).strip()


def _extract_contribution_points(text: str, *, limit: int = 8) -> list[str]:
    points: list[str] = []
    seen: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = re.sub(r"^[-*]\s+|^\d+\.\s+", "", line).strip()
        if normalized == line and not raw_line.lstrip().startswith(("-", "*")) and not re.match(r"^\s*\d+\.\s+", raw_line):
            continue
        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            points.append(normalized)
        if len(points) >= limit:
            break
    return points


def _infer_manuscript_type(project: Project, text: str) -> str:
    combined = f"{project.objective}\n{text}".lower()
    hits = sum(1 for hint in SYSTEM_PAPER_HINTS if hint in combined)
    return "system_paper" if hits >= 2 else "original_article"


def load_manuscript_context(session: Session, project: Project, profile: DatasetProfile) -> dict[str, object]:
    chunks = list(
        session.scalars(
            select(ArtifactChunk)
            .where(ArtifactChunk.project_id == project.id)
            .order_by(ArtifactChunk.role, ArtifactChunk.artifact_id, ArtifactChunk.ordinal)
        ).all()
    )
    narrative_chunks = [chunk for chunk in chunks if chunk.role == "narrative_brief"]
    supporting_chunks = [chunk for chunk in chunks if chunk.role == "supporting_doc"]
    background_chunks = [chunk for chunk in chunks if chunk.role == "background_reference"]

    narrative_text = _join_chunks(narrative_chunks, max_chars=9000)
    supporting_text = _join_chunks(supporting_chunks, max_chars=7000)
    background_text = _join_chunks(background_chunks, max_chars=5000)
    combined_text = "\n\n".join(part for part in [narrative_text, supporting_text] if part).strip()
    contribution_points = _extract_contribution_points(combined_text)
    manuscript_type = _infer_manuscript_type(project, combined_text)

    return {
        "preferred_manuscript_type": manuscript_type,
        "narrative_text": narrative_text,
        "supporting_text": supporting_text,
        "background_text": background_text,
        "contribution_points": contribution_points,
        "results_context": profile.summary_json.get("results_context", {}),
    }
