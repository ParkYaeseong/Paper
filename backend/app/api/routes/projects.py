from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.deps import require_user
from app.models import Artifact, Project
from app.schemas.project import ArtifactListResponse, ArtifactRead, ProjectCreate, ProjectListResponse, ProjectRead
from app.services.storage import save_upload_file


router = APIRouter(prefix="/projects", tags=["projects"])


def _is_admin(user: dict) -> bool:
    return str(user.get("role") or "").lower() == "admin"


def _get_project_or_403(session: Session, project_id: str, user: dict) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not _is_admin(user) and project.owner_sub != str(user.get("sub") or ""):
        raise HTTPException(status_code=403, detail="Access denied")
    return project


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
) -> Project:
    project = Project(
        owner_sub=str(user.get("sub") or ""),
        owner_username=str(user.get("username") or ""),
        title=payload.title.strip(),
        objective=payload.objective.strip(),
        status="draft",
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("", response_model=ProjectListResponse)
def list_projects(
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
) -> ProjectListResponse:
    query = select(Project).order_by(Project.created_at.desc())
    if not _is_admin(user):
        query = query.where(Project.owner_sub == str(user.get("sub") or ""))
    items = list(session.scalars(query).all())
    return ProjectListResponse(items=items)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: str,
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
) -> Project:
    return _get_project_or_403(session, project_id, user)


@router.post("/{project_id}/artifacts", response_model=ArtifactListResponse, status_code=status.HTTP_201_CREATED)
async def upload_artifacts(
    project_id: str,
    request: Request,
    files: list[UploadFile] = File(...),
    user: dict = Depends(require_user),
    session: Session = Depends(get_db_session),
) -> ArtifactListResponse:
    project = _get_project_or_403(session, project_id, user)
    settings = request.app.state.settings

    stored_items: list[Artifact] = []
    for upload in files:
        stored = await save_upload_file(settings, project.id, upload)
        artifact = Artifact(
            project_id=project.id,
            kind="upload",
            filename=str(stored["filename"]),
            content_type=str(stored["content_type"]),
            storage_path=str(stored["storage_path"]),
            size_bytes=int(stored["size_bytes"]),
            sha256=str(stored["sha256"]),
        )
        session.add(artifact)
        stored_items.append(artifact)
    session.commit()
    for item in stored_items:
        session.refresh(item)
    return ArtifactListResponse(items=[ArtifactRead.model_validate(item) for item in stored_items])
