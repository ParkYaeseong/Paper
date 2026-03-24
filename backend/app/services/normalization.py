from __future__ import annotations

import csv
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Artifact, DatasetProfile, Project


def _profile_version(session: Session, project_id: str) -> int:
    version = session.scalar(select(func.max(DatasetProfile.version)).where(DatasetProfile.project_id == project_id))
    return int(version or 0) + 1


def _summarize_csv(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    header = rows[0] if rows else []
    data_rows = rows[1:] if len(rows) > 1 else []
    numeric_columns: list[str] = []
    for idx, column in enumerate(header):
        values = [row[idx] for row in data_rows if len(row) > idx and row[idx] != ""]
        if values:
            try:
                [float(value) for value in values]
                numeric_columns.append(column)
            except ValueError:
                continue
    return {
        "filename": path.name,
        "row_count": len(data_rows),
        "column_count": len(header),
        "columns": header,
        "numeric_columns": numeric_columns,
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


def build_dataset_profile(project: Project, artifacts: list[Artifact]) -> dict[str, object]:
    table_summaries: list[dict[str, object]] = []
    note_summaries: list[dict[str, object]] = []
    file_types: dict[str, int] = {}

    for artifact in artifacts:
        path = Path(artifact.storage_path)
        suffix = path.suffix.lower() or "unknown"
        file_types[suffix] = file_types.get(suffix, 0) + 1
        if suffix == ".csv" and path.exists():
            table_summaries.append(_summarize_csv(path))
        elif path.exists():
            note_summaries.append(_summarize_generic(path))

    return {
        "project_title": project.title,
        "objective": project.objective,
        "dataset_summary": {
            "artifact_count": len(artifacts),
            "table_count": len(table_summaries),
            "file_types": file_types,
            "tables": table_summaries,
            "notes": note_summaries,
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
    profile = DatasetProfile(
        project_id=project.id,
        version=_profile_version(session, project.id),
        summary_json=build_dataset_profile(project, artifacts),
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
