from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_db_session
from app.deps import require_user
from app.models import CitationSlot, DatasetProfile, DraftSection, EvidenceMatch, ExportBundle, JobRun, Outline, Project, ReferenceRecord
from app.services.drafting import run_draft
from app.services.exporting import run_export
from app.services.grounding import run_grounding
from app.services.normalization import run_ingest
from app.services.planning import run_plan
from app.services.retrieval import run_retrieve


router = APIRouter(prefix="/projects/{project_id}", tags=["workspace"])


class ReviewSectionUpdate(BaseModel):
    content: str


class ReviewCitationUpdate(BaseModel):
    status: str
    selected_reference_ids_json: list[str] | None = None


def _is_admin(user: dict) -> bool:
    return str(user.get("role") or "").lower() == "admin"


def _project_or_403(session: Session, project_id: str, user: dict) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not _is_admin(user) and project.owner_sub != str(user.get("sub") or ""):
        raise HTTPException(status_code=403, detail="Access denied")
    return project


def _latest(session: Session, model, project_id: str):
    return session.scalars(select(model).where(model.project_id == project_id).order_by(model.created_at.desc())).first()


def _serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _serialize_project(project: Project) -> dict[str, object]:
    return {
        "id": project.id,
        "title": project.title,
        "objective": project.objective,
        "status": project.status,
        "owner_sub": project.owner_sub,
        "owner_username": project.owner_username,
        "created_at": _serialize_datetime(project.created_at),
        "updated_at": _serialize_datetime(project.updated_at),
    }


def _serialize_section(section: DraftSection) -> dict[str, object]:
    return {
        "id": section.id,
        "section_key": section.section_key,
        "heading": section.heading,
        "version": section.version,
        "content": section.content,
        "status": section.status,
        "created_at": _serialize_datetime(section.created_at),
        "updated_at": _serialize_datetime(section.updated_at),
    }


def _serialize_slot(slot: CitationSlot) -> dict[str, object]:
    return {
        "id": slot.id,
        "section_key": slot.section_key,
        "slot_key": slot.slot_key,
        "claim_text": slot.claim_text,
        "context_text": slot.context_text,
        "ordinal": slot.ordinal,
        "status": slot.status,
        "created_at": _serialize_datetime(slot.created_at),
        "updated_at": _serialize_datetime(slot.updated_at),
    }


def _serialize_reference(reference: ReferenceRecord) -> dict[str, object]:
    return {
        "id": reference.id,
        "source": reference.source,
        "external_id": reference.external_id,
        "title": reference.title,
        "abstract": reference.abstract,
        "authors_json": reference.authors_json,
        "venue": reference.venue,
        "year": reference.year,
        "doi": reference.doi,
        "url": reference.url,
    }


def _serialize_match(match: EvidenceMatch) -> dict[str, object]:
    return {
        "id": match.id,
        "citation_slot_id": match.citation_slot_id,
        "queries_json": match.queries_json,
        "candidate_reference_ids_json": match.candidate_reference_ids_json,
        "selected_reference_ids_json": match.selected_reference_ids_json,
        "support_score": match.support_score,
        "status": match.status,
        "notes": match.notes,
        "created_at": _serialize_datetime(match.created_at),
        "updated_at": _serialize_datetime(match.updated_at),
    }


def _serialize_job(job: JobRun) -> dict[str, object]:
    return {
        "id": job.id,
        "stage": job.stage,
        "status": job.status,
        "payload_json": job.payload_json,
        "result_json": job.result_json,
        "log_text": job.log_text,
        "started_at": _serialize_datetime(job.started_at),
        "finished_at": _serialize_datetime(job.finished_at),
        "created_at": _serialize_datetime(job.created_at),
        "updated_at": _serialize_datetime(job.updated_at),
    }


def _stage_dispatch(stage: str, session: Session, project: Project, settings: Settings):
    if stage == "ingest":
        return run_ingest(session, project)
    if stage == "plan":
        return run_plan(session, project)
    if stage == "draft":
        return run_draft(session, project)
    if stage == "retrieve":
        return run_retrieve(session, project)
    if stage == "ground":
        return run_grounding(session, project.id)
    if stage == "export":
        return run_export(session, project, settings)
    raise HTTPException(status_code=400, detail="Unknown pipeline stage")


def _bundle_download_urls(project_id: str, bundle: ExportBundle | None) -> dict[str, str]:
    if bundle is None:
        return {}
    return {
        "markdown": f"/api/projects/{project_id}/exports/{bundle.id}/markdown",
        "bibtex": f"/api/projects/{project_id}/exports/{bundle.id}/bibtex",
        "json": f"/api/projects/{project_id}/exports/{bundle.id}/json",
        "docx": f"/api/projects/{project_id}/exports/{bundle.id}/docx",
    }


@router.get("/workspace")
def get_workspace(
    project_id: str,
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
):
    project = _project_or_403(session, project_id, user)
    profile = _latest(session, DatasetProfile, project.id)
    outline = _latest(session, Outline, project.id)
    export_bundle = _latest(session, ExportBundle, project.id)
    sections = list(session.scalars(select(DraftSection).where(DraftSection.project_id == project.id).order_by(DraftSection.section_key, DraftSection.version)))
    slots = list(session.scalars(select(CitationSlot).where(CitationSlot.project_id == project.id).order_by(CitationSlot.section_key, CitationSlot.ordinal)))
    references = list(session.scalars(select(ReferenceRecord).where(ReferenceRecord.project_id == project.id).order_by(ReferenceRecord.created_at)))
    matches = list(session.scalars(select(EvidenceMatch).where(EvidenceMatch.project_id == project.id).order_by(EvidenceMatch.created_at)))
    jobs = list(session.scalars(select(JobRun).where(JobRun.project_id == project.id).order_by(JobRun.created_at)))
    return {
        "project": _serialize_project(project),
        "dataset_profile": None if profile is None else {"id": profile.id, "version": profile.version, "summary_json": profile.summary_json},
        "outline": None
        if outline is None
        else {
            "id": outline.id,
            "version": outline.version,
            "manuscript_type": outline.manuscript_type,
            "title_candidates_json": outline.title_candidates_json,
            "outline_json": outline.outline_json,
        },
        "draft_sections": [_serialize_section(section) for section in sections],
        "citation_slots": [_serialize_slot(slot) for slot in slots],
        "reference_records": [_serialize_reference(reference) for reference in references],
        "evidence_matches": [_serialize_match(match) for match in matches],
        "export_bundle": None
        if export_bundle is None
        else {
            "id": export_bundle.id,
            "status": export_bundle.status,
            "manifest_json": export_bundle.manifest_json,
            "download_urls": _bundle_download_urls(project.id, export_bundle),
        },
        "jobs": [_serialize_job(job) for job in jobs],
    }


@router.post("/pipeline/{stage}")
def run_pipeline_stage(
    project_id: str,
    stage: str,
    request: Request,
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
):
    project = _project_or_403(session, project_id, user)
    job = JobRun(project_id=project.id, stage=stage, status="running", started_at=datetime.now(timezone.utc))
    session.add(job)
    session.commit()
    session.refresh(job)
    try:
        result = _stage_dispatch(stage, session, project, request.app.state.settings)
        job.status = "succeeded"
        job.result_json = {"type": result.__class__.__name__}
        job.finished_at = datetime.now(timezone.utc)
        session.add(job)
        session.commit()
        session.refresh(job)
        return {"ok": True, "job": _serialize_job(job)}
    except Exception as exc:
        job.status = "failed"
        job.log_text = str(exc)
        job.finished_at = datetime.now(timezone.utc)
        session.add(job)
        session.commit()
        session.refresh(job)
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/draft-sections/{section_id}")
def update_draft_section(
    project_id: str,
    section_id: str,
    payload: ReviewSectionUpdate,
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
):
    project = _project_or_403(session, project_id, user)
    section = session.get(DraftSection, section_id)
    if section is None or section.project_id != project.id:
        raise HTTPException(status_code=404, detail="Draft section not found")
    section.content = payload.content
    section.status = "reviewed"
    session.add(section)
    session.commit()
    session.refresh(section)
    return {"ok": True, "section": _serialize_section(section)}


@router.patch("/citation-slots/{slot_id}")
def update_citation_slot(
    project_id: str,
    slot_id: str,
    payload: ReviewCitationUpdate,
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
):
    project = _project_or_403(session, project_id, user)
    slot = session.get(CitationSlot, slot_id)
    if slot is None or slot.project_id != project.id:
        raise HTTPException(status_code=404, detail="Citation slot not found")
    slot.status = payload.status
    match = session.scalars(
        select(EvidenceMatch).where(EvidenceMatch.project_id == project.id, EvidenceMatch.citation_slot_id == slot.id)
    ).first()
    if match is not None:
        match.status = payload.status
        if payload.selected_reference_ids_json is not None:
            match.selected_reference_ids_json = payload.selected_reference_ids_json
        session.add(match)
    session.add(slot)
    session.commit()
    session.refresh(slot)
    return {"ok": True, "slot": _serialize_slot(slot)}


@router.get("/exports/{bundle_id}/{kind}")
def download_export(
    project_id: str,
    bundle_id: str,
    kind: str,
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
):
    project = _project_or_403(session, project_id, user)
    bundle = session.get(ExportBundle, bundle_id)
    if bundle is None or bundle.project_id != project.id:
        raise HTTPException(status_code=404, detail="Export bundle not found")
    manifest = bundle.manifest_json or {}
    path_map = {
        "markdown": manifest.get("markdown_path"),
        "bibtex": manifest.get("bibtex_path"),
        "json": manifest.get("json_path"),
        "docx": manifest.get("docx_path"),
    }
    raw_path = path_map.get(kind)
    if not raw_path:
        raise HTTPException(status_code=404, detail="Export artifact not found")
    path = Path(str(raw_path))
    if not path.exists():
        raise HTTPException(status_code=404, detail="Export file missing")
    media_type = {
        "markdown": "text/markdown; charset=utf-8",
        "bibtex": "application/x-bibtex",
        "json": "application/json",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }.get(kind, "application/octet-stream")
    return FileResponse(path, media_type=media_type, filename=path.name)
