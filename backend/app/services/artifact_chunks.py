from __future__ import annotations

import json
import re
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.artifact_roles import BACKGROUND_REFERENCE, NARRATIVE_BRIEF, RESULTS_TABLE, SUPPORTING_DOC, normalize_artifact_role
from app.models import Artifact, ArtifactChunk


HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*\S)\s*$")


def _load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return path.read_text(encoding="utf-8", errors="ignore")
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return path.read_text(encoding="utf-8", errors="ignore")


def _normalize_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _split_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    heading = ""
    lines: list[str] = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            content = "\n".join(lines).strip()
            if heading or content:
                sections.append((heading, content))
            heading = match.group(2).strip()
            lines = []
            continue
        lines.append(line)

    content = "\n".join(lines).strip()
    if heading or content:
        sections.append((heading, content))
    return sections or [("", text)]


def _split_long_text(text: str, *, max_chars: int = 1800) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    if not paragraphs:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for paragraph in paragraphs:
        addition = len(paragraph) + (2 if current else 0)
        if current and current_length + addition > max_chars:
            chunks.append("\n\n".join(current).strip())
            current = [paragraph]
            current_length = len(paragraph)
            continue
        current.append(paragraph)
        current_length += addition
    if current:
        chunks.append("\n\n".join(current).strip())
    return chunks


def build_text_chunks(path: Path) -> list[dict[str, str | int]]:
    text = _normalize_text(_load_text(path))
    if not text:
        return []

    chunks: list[dict[str, str | int]] = []
    ordinal = 1
    for heading, section_text in _split_sections(text):
        section_source = section_text or heading
        for content in _split_long_text(section_source):
            chunks.append(
                {
                    "ordinal": ordinal,
                    "heading": heading,
                    "content": content,
                }
            )
            ordinal += 1
    return chunks


def rebuild_artifact_chunks(session: Session, project_id: str, artifacts: list[Artifact]) -> None:
    session.execute(delete(ArtifactChunk).where(ArtifactChunk.project_id == project_id))
    text_roles = {NARRATIVE_BRIEF, SUPPORTING_DOC, BACKGROUND_REFERENCE}

    for artifact in artifacts:
        role = normalize_artifact_role((artifact.metadata_json or {}).get("role"))
        if role not in text_roles:
            continue
        path = Path(artifact.storage_path)
        if not path.exists():
            continue
        for chunk in build_text_chunks(path):
            session.add(
                ArtifactChunk(
                    project_id=project_id,
                    artifact_id=artifact.id,
                    role=role,
                    ordinal=int(chunk["ordinal"]),
                    heading=str(chunk["heading"] or ""),
                    content=str(chunk["content"] or ""),
                )
            )
    session.flush()


def list_artifact_chunks(session: Session, project_id: str, role: str) -> list[ArtifactChunk]:
    return list(
        session.scalars(
            select(ArtifactChunk)
            .where(
                ArtifactChunk.project_id == project_id,
                ArtifactChunk.role == normalize_artifact_role(role),
            )
            .order_by(ArtifactChunk.artifact_id, ArtifactChunk.ordinal)
        ).all()
    )
