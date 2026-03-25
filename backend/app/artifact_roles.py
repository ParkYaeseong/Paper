from __future__ import annotations

from pathlib import Path


NARRATIVE_BRIEF = "narrative_brief"
SUPPORTING_DOC = "supporting_doc"
RESULTS_TABLE = "results_table"
BACKGROUND_REFERENCE = "background_reference"

ARTIFACT_ROLES = {
    NARRATIVE_BRIEF,
    SUPPORTING_DOC,
    RESULTS_TABLE,
    BACKGROUND_REFERENCE,
}


def normalize_artifact_role(value: str | None) -> str:
    role = str(value or "").strip().lower()
    if role in ARTIFACT_ROLES:
        return role
    return SUPPORTING_DOC


def infer_artifact_role(filename: str, *, requested_role: str | None = None) -> str:
    normalized = str(requested_role or "").strip()
    if normalized:
        return normalize_artifact_role(normalized)

    suffix = Path(filename).suffix.lower()
    if suffix in {".csv", ".tsv", ".xlsx", ".xls"}:
        return RESULTS_TABLE
    if suffix in {".md", ".txt", ".doc", ".docx"}:
        return SUPPORTING_DOC
    return SUPPORTING_DOC
