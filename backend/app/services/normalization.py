from __future__ import annotations

import csv
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.artifact_roles import (
    BACKGROUND_REFERENCE,
    NARRATIVE_BRIEF,
    RESULTS_TABLE,
    SUPPORTING_DOC,
    normalize_artifact_role,
)
from app.models import Artifact, ArtifactChunk, DatasetProfile, Project
from app.services.artifact_chunks import rebuild_artifact_chunks


def _profile_version(session: Session, project_id: str) -> int:
    version = session.scalar(select(func.max(DatasetProfile.version)).where(DatasetProfile.project_id == project_id))
    return int(version or 0) + 1


def _summarize_csv(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        data_rows = list(reader)

    numeric_columns: list[str] = []
    numeric_summaries: dict[str, dict[str, float]] = {}
    sample_rows: list[dict[str, str]] = []
    for row in data_rows[:5]:
        sample_rows.append(
            {
                column: str(row.get(column) or "").strip()
                for column in header
            }
        )
    for column in header:
        values = [str(row.get(column) or "").strip() for row in data_rows if str(row.get(column) or "").strip() != ""]
        if values:
            try:
                numeric_values = [float(value) for value in values]
                numeric_columns.append(column)
                numeric_summaries[column] = {
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": round(sum(numeric_values) / len(numeric_values), 6),
                }
            except ValueError:
                continue
    return {
        "filename": path.name,
        "row_count": len(data_rows),
        "column_count": len(header),
        "columns": header,
        "numeric_columns": numeric_columns,
        "numeric_summaries": numeric_summaries,
        "sample_rows": sample_rows,
    }


def _summarize_generic(path: Path) -> dict[str, object]:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        preview = path.read_text(encoding="utf-8", errors="ignore")[:500]
        return {"filename": path.name, "preview": preview, "type": suffix.lstrip(".")}
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            keys = list(payload)[:20] if isinstance(payload, dict) else []
        except Exception:
            keys = []
        return {"filename": path.name, "json_keys": keys, "type": "json"}
    return {"filename": path.name, "type": suffix.lstrip(".") or "binary"}


def _summarize_json_results(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"filename": path.name, "type": "json", "top_level": "invalid"}
    if isinstance(payload, list):
        row_count = len(payload)
        first = payload[0] if payload else {}
        columns = list(first.keys())[:20] if isinstance(first, dict) else []
        sample_rows = payload[:5] if all(isinstance(item, dict) for item in payload[:5]) else []
        return {
            "filename": path.name,
            "type": "json",
            "top_level": "list",
            "row_count": row_count,
            "columns": columns,
            "sample_rows": sample_rows,
        }
    if isinstance(payload, dict):
        return {
            "filename": path.name,
            "type": "json",
            "top_level": "dict",
            "json_keys": list(payload.keys())[:20],
        }
    return {"filename": path.name, "type": "json", "top_level": type(payload).__name__}


def _artifact_chunks_summary(artifacts: list[Artifact], chunks: list[ArtifactChunk]) -> dict[str, object]:
    chunks_by_artifact: dict[str, list[ArtifactChunk]] = {}
    for chunk in chunks:
        chunks_by_artifact.setdefault(chunk.artifact_id, []).append(chunk)

    return {
        "artifact_count": len(artifacts),
        "artifacts": [
            {
                "artifact_id": artifact.id,
                "filename": artifact.filename,
                "role": artifact.role,
                "chunk_count": len(chunks_by_artifact.get(artifact.id, [])),
                "headings": [
                    chunk.heading
                    for chunk in chunks_by_artifact.get(artifact.id, [])
                    if chunk.heading
                ][:12],
            }
            for artifact in artifacts
        ],
    }


def build_dataset_profile(session: Session, project: Project, artifacts: list[Artifact]) -> dict[str, object]:
    table_summaries: list[dict[str, object]] = []
    file_types: dict[str, int] = {}
    role_counts: dict[str, int] = {}
    narrative_artifacts: list[Artifact] = []
    supporting_artifacts: list[Artifact] = []
    background_artifacts: list[Artifact] = []

    for artifact in artifacts:
        path = Path(artifact.storage_path)
        suffix = path.suffix.lower() or "unknown"
        file_types[suffix] = file_types.get(suffix, 0) + 1
        role = normalize_artifact_role((artifact.metadata_json or {}).get("role"))
        role_counts[role] = role_counts.get(role, 0) + 1
        if role == RESULTS_TABLE and path.exists():
            if suffix == ".csv":
                summary = _summarize_csv(path)
            elif suffix == ".json":
                summary = _summarize_json_results(path)
            else:
                summary = _summarize_generic(path)
            summary["role"] = role
            table_summaries.append(summary)
        elif role == NARRATIVE_BRIEF:
            narrative_artifacts.append(artifact)
        elif role == SUPPORTING_DOC:
            supporting_artifacts.append(artifact)
        elif role == BACKGROUND_REFERENCE:
            background_artifacts.append(artifact)

    chunks = list(
        session.scalars(
            select(ArtifactChunk)
            .where(ArtifactChunk.project_id == project.id)
            .order_by(ArtifactChunk.role, ArtifactChunk.artifact_id, ArtifactChunk.ordinal)
        ).all()
    )
    narrative_chunks = [chunk for chunk in chunks if chunk.role == NARRATIVE_BRIEF]
    supporting_chunks = [chunk for chunk in chunks if chunk.role == SUPPORTING_DOC]
    background_chunks = [chunk for chunk in chunks if chunk.role == BACKGROUND_REFERENCE]

    return {
        "project_title": project.title,
        "objective": project.objective,
        "project_brief": {
            "title": project.title,
            "objective": project.objective,
        },
        "dataset_summary": {
            "artifact_count": len(artifacts),
            "table_count": len(table_summaries),
            "file_types": file_types,
            "role_counts": role_counts,
            "tables": table_summaries,
            "source_artifacts": [
                {
                    "artifact_id": artifact.id,
                    "filename": artifact.filename,
                    "role": artifact.role,
                    "sha256": artifact.sha256,
                }
                for artifact in artifacts
            ],
        },
        "narrative_context": _artifact_chunks_summary(narrative_artifacts, narrative_chunks),
        "supporting_context": _artifact_chunks_summary(supporting_artifacts, supporting_chunks),
        "background_context": _artifact_chunks_summary(background_artifacts, background_chunks),
        "results_context": {
            "table_count": len(table_summaries),
            "tables": table_summaries,
        },
        "main_findings": [
            "Uploaded datasets were normalized into a project profile for manuscript planning.",
            "The project workspace can now draft manuscript sections from structured input context.",
        ],
        "limitations": [
            "Automated summaries should be reviewed by a domain expert before submission.",
        ],
    }


def run_ingest(session: Session, project: Project) -> DatasetProfile:
    artifacts = list(session.scalars(select(Artifact).where(Artifact.project_id == project.id).order_by(Artifact.created_at)))
    rebuild_artifact_chunks(session, project.id, artifacts)
    profile = DatasetProfile(
        project_id=project.id,
        version=_profile_version(session, project.id),
        summary_json=build_dataset_profile(session, project, artifacts),
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
