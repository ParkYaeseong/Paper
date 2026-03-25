from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile

from app.config import Settings


def _project_root(settings: Settings, project_id: str) -> Path:
    return Path(settings.storage_root).expanduser().resolve() / "projects" / project_id


async def save_upload_file(settings: Settings, project_id: str, upload: UploadFile) -> dict[str, object]:
    project_root = _project_root(settings, project_id)
    project_root.mkdir(parents=True, exist_ok=True)

    raw = await upload.read()
    filename = upload.filename or f"upload-{uuid.uuid4()}"
    safe_name = Path(filename).name
    target = project_root / str(uuid.uuid4()) / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)

    return {
        "filename": safe_name,
        "storage_path": str(target),
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "content_type": upload.content_type or "application/octet-stream",
    }


def delete_stored_file(storage_path: str) -> None:
    path = Path(storage_path)
    if path.exists() and path.is_file():
        path.unlink()
    parent = path.parent
    if parent.exists() and parent.is_dir():
        try:
            parent.rmdir()
        except OSError:
            pass


def delete_project_storage(settings: Settings, project_id: str) -> None:
    shutil.rmtree(_project_root(settings, project_id), ignore_errors=True)


def save_generated_file(
    settings: Settings,
    project_id: str,
    source_path: str | Path,
    *,
    subdir: str = "generated",
    filename: str | None = None,
    content_type: str = "image/png",
) -> dict[str, object]:
    project_root = _project_root(settings, project_id)
    project_root.mkdir(parents=True, exist_ok=True)

    source = Path(source_path)
    raw = source.read_bytes()
    safe_name = Path(filename or source.name or f"generated-{uuid.uuid4()}").name
    target = project_root / subdir / str(uuid.uuid4()) / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

    return {
        "filename": safe_name,
        "storage_path": str(target),
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "content_type": content_type,
    }
