from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from app.auth import (
    account_console_url,
    claims_to_user,
    exchange_oidc_code,
    get_oidc_discovery,
    issue_session_cookie,
    load_oidc_settings,
    verify_oidc_token,
)
from app.config import Settings
from app.deps import get_optional_user


router = APIRouter(prefix="/auth", tags=["auth"])


class OIDCExchangeRequest(BaseModel):
    code: str
    redirect_uri: str
    code_verifier: str | None = None


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _oidc_settings(request: Request):
    return load_oidc_settings(_settings(request))


@router.get("/oidc/config")
def auth_oidc_config(request: Request) -> dict[str, object]:
    oidc = _oidc_settings(request)
    if oidc is None:
        return {"ok": True, "enabled": False}
    try:
        discovery = get_oidc_discovery(oidc)
        authorization_endpoint = str(discovery.get("authorization_endpoint") or "")
        end_session_endpoint = str(discovery.get("end_session_endpoint") or "")
    except Exception:
        authorization_endpoint = ""
        end_session_endpoint = ""
    return {
        "ok": True,
        "enabled": True,
        "issuer": oidc.issuer,
        "client_id": oidc.client_id,
        "scopes": oidc.scopes,
        "provider_name": oidc.provider_name,
        "authorization_endpoint": authorization_endpoint,
        "end_session_endpoint": end_session_endpoint,
        "account_url": account_console_url(oidc),
    }


@router.post("/oidc/exchange")
def auth_oidc_exchange(body: OIDCExchangeRequest, request: Request, response: Response) -> dict[str, object]:
    oidc = _oidc_settings(request)
    if oidc is None:
        raise HTTPException(status_code=400, detail="OIDC disabled")
    token_data = exchange_oidc_code(
        oidc,
        code=body.code,
        redirect_uri=body.redirect_uri,
        code_verifier=body.code_verifier,
    )
    raw_token = str(token_data.get("id_token") or token_data.get("access_token") or "").strip()
    if not raw_token:
        raise HTTPException(status_code=400, detail="OIDC token exchange returned no token")
    claims = verify_oidc_token(raw_token, oidc)
    user = claims_to_user(claims, client_id=oidc.client_id)
    settings = _settings(request)
    response.set_cookie(
        settings.session_cookie_name,
        issue_session_cookie(settings.session_secret, user, ttl_s=settings.session_ttl_s),
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        max_age=settings.session_ttl_s,
        path="/",
    )
    return {"ok": True, "user": user}


@router.get("/me")
def auth_me(request: Request, user: dict | None = Depends(get_optional_user)) -> dict[str, object]:
    settings = _settings(request)
    oidc = load_oidc_settings(settings)
    if oidc is None:
        return {"ok": True, "enabled": False, "user": None}
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return {"ok": True, "enabled": True, "user": user}


@router.post("/logout")
def auth_logout(request: Request, response: Response) -> dict[str, object]:
    settings = _settings(request)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return {"ok": True}
