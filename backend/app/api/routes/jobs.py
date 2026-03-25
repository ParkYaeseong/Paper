from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.workspace import _project_or_403, _serialize_job
from app.db import get_db_session
from app.deps import require_user
from app.models import JobRun


router = APIRouter(prefix="/projects/{project_id}", tags=["jobs"])


@router.get("/jobs")
def list_jobs(
    project_id: str,
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
):
    project = _project_or_403(session, project_id, user)
    jobs = list(
        session.scalars(
            select(JobRun).where(JobRun.project_id == project.id).order_by(JobRun.created_at.desc())
        ).all()
    )
    return {"items": [_serialize_job(job) for job in jobs]}


@router.get("/jobs/{job_id}")
def get_job(
    project_id: str,
    job_id: str,
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
):
    project = _project_or_403(session, project_id, user)
    job = session.get(JobRun, job_id)
    if job is None or job.project_id != project.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": _serialize_job(job)}
