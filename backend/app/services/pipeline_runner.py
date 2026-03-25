from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import SessionLocal
from app.models import CitationSlot, DatasetProfile, DraftSection, EvidenceMatch, JobRun, Outline, Project
from app.services.drafting import run_draft
from app.services.exporting import run_export
from app.services.figures import run_generate_figures
from app.services.grounding import run_grounding
from app.services.normalization import run_ingest
from app.services.planning import run_plan
from app.services.quality import run_quality_audit
from app.services.retrieval import run_retrieve


ACTIVE_JOB_STATUSES = {"queued", "running"}
PIPELINE_STAGES = {"ingest", "plan", "draft", "retrieve", "ground", "evidence", "quality", "figures", "run_all", "export"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _latest(session: Session, model, project_id: str):
    return session.scalars(select(model).where(model.project_id == project_id).order_by(model.created_at.desc())).first()


def get_active_stage_job(session: Session, project_id: str, stage: str) -> JobRun | None:
    return session.scalars(
        select(JobRun)
        .where(
            JobRun.project_id == project_id,
            JobRun.stage == stage,
            JobRun.status.in_(ACTIVE_JOB_STATUSES),
        )
        .order_by(JobRun.created_at.desc())
    ).first()


def ensure_stage_prerequisites(session: Session, project_id: str, stage: str) -> None:
    if stage not in PIPELINE_STAGES:
        raise ValueError("Unknown pipeline stage")
    if stage in {"ingest", "run_all"}:
        return
    if stage == "plan" and _latest(session, DatasetProfile, project_id) is None:
        raise ValueError("Ingest must complete before planning")
    if stage == "draft":
        if _latest(session, DatasetProfile, project_id) is None or _latest(session, Outline, project_id) is None:
            raise ValueError("Planning must complete before drafting")
    if stage in {"retrieve", "evidence"}:
        slots = session.scalars(select(CitationSlot).where(CitationSlot.project_id == project_id)).first()
        if slots is None:
            raise ValueError("Planning must create citation slots before retrieval")
    if stage == "ground":
        match = session.scalars(select(EvidenceMatch).where(EvidenceMatch.project_id == project_id)).first()
        if match is None:
            raise ValueError("Retrieval must complete before grounding")
    if stage == "export":
        section = session.scalars(select(DraftSection).where(DraftSection.project_id == project_id)).first()
        if section is None:
            raise ValueError("Drafting must complete before export")
    if stage == "quality":
        section = session.scalars(select(DraftSection).where(DraftSection.project_id == project_id)).first()
        if section is None:
            raise ValueError("Drafting must complete before quality audit")
    if stage == "figures":
        section = session.scalars(select(DraftSection).where(DraftSection.project_id == project_id)).first()
        if section is None:
            raise ValueError("Drafting must complete before figure generation")


def _update_job_log(session: Session, job_id: str | None, message: str) -> None:
    if not job_id:
        return
    job = session.get(JobRun, job_id)
    if job is None:
        return
    job.log_text = message
    session.add(job)
    session.commit()


def run_pipeline_stage(
    session: Session,
    project: Project,
    settings: Settings,
    stage: str,
    *,
    payload: dict[str, Any] | None = None,
    job_id: str | None = None,
):
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
    if stage == "evidence":
        run_retrieve(session, project)
        return run_grounding(session, project.id)
    if stage == "quality":
        return run_quality_audit(session, project)
    if stage == "figures":
        return run_generate_figures(session, project, settings)
    if stage == "run_all":
        completed_stages: list[str] = []
        for substage in ["ingest", "plan", "draft", "evidence", "quality", "figures", "quality"]:
            _update_job_log(session, job_id, f"Running {substage}")
            ensure_stage_prerequisites(session, project.id, substage)
            run_pipeline_stage(session, project, settings, substage, payload=payload, job_id=job_id)
            completed_stages.append(substage)
        _update_job_log(session, job_id, "Run All completed")
        return {"completed_stages": completed_stages}
    if stage == "export":
        mode = str((payload or {}).get("mode") or "draft").lower()
        return run_export(session, project, settings, mode=mode)
    raise ValueError("Unknown pipeline stage")


def _serialize_result(result: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": result.__class__.__name__}
    result_id = getattr(result, "id", None)
    if result_id is not None:
        payload["id"] = str(result_id)
    if isinstance(result, list):
        payload["count"] = len(result)
    if isinstance(result, dict):
        payload.update(result)
    return payload


def process_pipeline_job(
    job_id: str,
    *,
    session_factory: Callable[[], Session] | None = None,
    settings: Settings | None = None,
) -> None:
    session_factory = session_factory or SessionLocal
    settings = settings or get_settings()

    with session_factory() as session:
        job = session.get(JobRun, job_id)
        if job is None:
            return
        project = session.get(Project, job.project_id)
        if project is None:
            job.status = "failed"
            job.log_text = "Project not found"
            job.finished_at = _utcnow()
            session.add(job)
            session.commit()
            return

        job.status = "running"
        job.started_at = job.started_at or _utcnow()
        session.add(job)
        session.commit()

        try:
            ensure_stage_prerequisites(session, project.id, job.stage)
            result = run_pipeline_stage(session, project, settings, job.stage, payload=job.payload_json or {}, job_id=job.id)
            job = session.get(JobRun, job_id)
            if job is None:
                return
            job.status = "succeeded"
            job.result_json = _serialize_result(result)
            job.finished_at = _utcnow()
            session.add(job)
            session.commit()
        except Exception as exc:
            session.rollback()
            job = session.get(JobRun, job_id)
            if job is None:
                return
            job.status = "failed"
            job.log_text = str(exc)
            job.finished_at = _utcnow()
            session.add(job)
            session.commit()
