from __future__ import annotations

from fastapi import APIRouter


router = APIRouter()


@router.get("/healthz")
def get_health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "paper-api",
        "status": "healthy",
    }
