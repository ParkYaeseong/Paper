from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import time
from typing import Any

import requests

from app.config import Settings


@dataclass(frozen=True)
class OIDCSettings:
    issuer: str
    client_id: str
    audience: str | None
    scopes: str
    provider_name: str
    jwks_url: str | None
    algorithms: tuple[str, ...]


def _normalize_issuer(issuer: str) -> str:
    normalized = issuer.strip().rstrip("/")
    suffix = "/.well-known/openid-configuration"
    if normalized.endswith(suffix):
        normalized = normalized[: -len(suffix)].rstrip("/")
    if normalized and "://" not in normalized:
        normalized = f"https://{normalized}"
    return normalized


def load_oidc_settings(settings: Settings) -> OIDCSettings | None:
    if not settings.oidc_issuer or not settings.oidc_client_id:
        return None
    algorithms = tuple(item.strip() for item in settings.oidc_algorithms.split(",") if item.strip())
    audience = settings.oidc_audience.strip() or settings.oidc_client_id
    return OIDCSettings(
        issuer=_normalize_issuer(settings.oidc_issuer),
        client_id=settings.oidc_client_id.strip(),
        audience=audience,
        scopes=settings.oidc_scopes.strip() or "openid profile email",
        provider_name=settings.oidc_provider_name.strip() or "KBF SSO",
        jwks_url=settings.oidc_jwks_url.strip() or None,
        algorithms=algorithms or ("RS256",),
    )


def get_oidc_discovery(settings: OIDCSettings) -> dict[str, Any]:
    response = requests.get(f"{settings.issuer}/.well-known/openid-configuration", timeout=10)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("invalid OIDC discovery payload")
    return payload


def account_console_url(settings: OIDCSettings) -> str:
    issuer = settings.issuer.rstrip("/")
    if not issuer:
        return ""
    return f"{issuer}/account/"


def _extract_audiences(claims: dict[str, Any]) -> set[str]:
    raw = claims.get("aud")
    if isinstance(raw, str):
        normalized = raw.strip()
        return {normalized} if normalized else set()
    if isinstance(raw, list):
        return {str(item).strip() for item in raw if str(item).strip()}
    return set()


def _claims_match_expected_client(claims: dict[str, Any], settings: OIDCSettings) -> bool:
    if settings.audience and settings.audience in _extract_audiences(claims):
        return True
    azp = claims.get("azp")
    return isinstance(azp, str) and azp.strip() == settings.client_id


def verify_oidc_token(token: str, settings: OIDCSettings) -> dict[str, Any]:
    from jose import jwt

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    jwks_uri = settings.jwks_url
    if not jwks_uri:
        discovery = get_oidc_discovery(settings)
        jwks_uri = str(discovery.get("jwks_uri") or "").strip()
    if not jwks_uri:
        raise ValueError("OIDC JWKS URI is not configured")

    jwks_response = requests.get(jwks_uri, timeout=10)
    jwks_response.raise_for_status()
    jwks_payload = jwks_response.json()
    keys = jwks_payload.get("keys") if isinstance(jwks_payload, dict) else None
    if not isinstance(keys, list) or not keys:
        raise ValueError("OIDC JWKS payload is invalid")

    signing_key = None
    for key in keys:
        if isinstance(key, dict) and key.get("kid") == kid:
            signing_key = key
            break
    if signing_key is None and len(keys) == 1 and isinstance(keys[0], dict):
        signing_key = keys[0]
    if signing_key is None:
        raise ValueError("unable to select OIDC signing key")

    claims = jwt.decode(
        token,
        signing_key,
        algorithms=list(settings.algorithms),
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": False,
            "verify_iss": False,
            "verify_at_hash": False,
        },
    )
    if _normalize_issuer(str(claims.get("iss") or "")) != settings.issuer:
        raise ValueError("invalid OIDC issuer")
    if not _claims_match_expected_client(claims, settings):
        raise ValueError("invalid OIDC audience")
    if not isinstance(claims, dict):
        raise ValueError("invalid OIDC claims")
    return claims


def exchange_oidc_code(
    settings: OIDCSettings,
    *,
    code: str,
    redirect_uri: str,
    code_verifier: str | None = None,
) -> dict[str, Any]:
    discovery = get_oidc_discovery(settings)
    token_endpoint = str(discovery.get("token_endpoint") or "").strip()
    if not token_endpoint:
        raise ValueError("OIDC token endpoint is unavailable")

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": settings.client_id,
    }
    if code_verifier:
        payload["code_verifier"] = code_verifier

    response = requests.post(token_endpoint, data=payload, timeout=10)
    token_data = response.json() if response.content else {}
    if response.status_code >= 400:
        detail = token_data.get("error_description") or token_data.get("error") or f"HTTP {response.status_code}"
        raise ValueError(str(detail))
    if not isinstance(token_data, dict):
        raise ValueError("invalid OIDC token response")
    return token_data


def get_client_roles(claims: dict[str, Any], client_id: str) -> set[str]:
    resource_access = claims.get("resource_access")
    if not isinstance(resource_access, dict):
        return set()
    client_block = resource_access.get(client_id)
    if not isinstance(client_block, dict):
        return set()
    roles = client_block.get("roles")
    if not isinstance(roles, list):
        return set()
    return {str(role) for role in roles}


def claims_to_user(claims: dict[str, Any], client_id: str = "paper") -> dict[str, Any]:
    username = (
        str(claims.get("preferred_username") or "").strip()
        or str(claims.get("email") or "").strip()
        or str(claims.get("sub") or "").strip()
    )
    if not username:
        raise ValueError("missing subject")
    roles = get_client_roles(claims, client_id)
    role = "admin" if "paper-admin" in roles else "user"
    return {
        "sub": str(claims.get("sub") or ""),
        "username": username,
        "email": str(claims.get("email") or ""),
        "name": str(claims.get("name") or claims.get("given_name") or username),
        "role": role,
    }


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def issue_session_cookie(secret: str, user: dict[str, Any], *, ttl_s: int) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user.get("sub") or ""),
        "username": str(user.get("username") or ""),
        "email": str(user.get("email") or ""),
        "name": str(user.get("name") or ""),
        "role": "admin" if str(user.get("role") or "").lower() == "admin" else "user",
        "iat": now,
        "exp": now + int(ttl_s),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    body = _b64url_encode(raw)
    sig = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{_b64url_encode(sig)}"


def verify_session_cookie(secret: str, token: str) -> dict[str, Any] | None:
    parts = str(token or "").split(".")
    if len(parts) != 2:
        return None
    body, sig_raw = parts
    try:
        expected = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
        sig = _b64url_decode(sig_raw)
    except Exception:
        return None
    if not hmac.compare_digest(expected, sig):
        return None
    try:
        payload = json.loads(_b64url_decode(body))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None
    return payload
