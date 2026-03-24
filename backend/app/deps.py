from __future__ import annotations

from fastapi import HTTPException, Request

from app.auth import verify_session_cookie
from app.config import Settings


def _get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_optional_user(request: Request) -> dict | None:
    settings = _get_settings(request)
    if not settings.oidc_issuer or not settings.oidc_client_id:
        return None
    token = str(request.cookies.get(settings.session_cookie_name) or "").strip()
    if not token:
        return None
    return verify_session_cookie(settings.session_secret, token)


def require_user(request: Request) -> dict:
    user = get_optional_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
