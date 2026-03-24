from __future__ import annotations

import hashlib
from pathlib import Path
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
    target = project_root / safe_name
    target.write_bytes(raw)

    return {
        "filename": safe_name,
        "storage_path": str(target),
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "content_type": upload.content_type or "application/octet-stream",
    }
