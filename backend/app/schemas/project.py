from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    title: str
    objective: str = ""


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    objective: str
    status: str
    owner_sub: str
    owner_username: str
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectRead]


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    kind: str
    filename: str
    content_type: str
    storage_path: str
    size_bytes: int
    sha256: str
    created_at: datetime
    updated_at: datetime


class ArtifactListResponse(BaseModel):
    items: list[ArtifactRead]
