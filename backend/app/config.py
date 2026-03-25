from __future__ import annotations

from dataclasses import dataclass
import os


def _env(key: str, default: str) -> str:
    value = os.getenv(key)
    if value is None:
        return default
    stripped = value.strip()
    return stripped or default


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    redis_url: str
    oidc_issuer: str
    oidc_client_id: str
    oidc_audience: str
    oidc_scopes: str
    oidc_provider_name: str
    oidc_jwks_url: str
    oidc_algorithms: str
    session_secret: str
    session_ttl_s: int
    session_cookie_name: str
    session_cookie_secure: bool
    storage_root: str
    paperbanana_root: str
    paperbanana_python: str
    paperbanana_candidates: int


def get_settings() -> Settings:
    return Settings(
        app_name=_env("PAPER_APP_NAME", "Paper API"),
        app_version=_env("PAPER_APP_VERSION", "0.1.0"),
        redis_url=_env("PAPER_REDIS_URL", "redis://localhost:6379/0"),
        oidc_issuer=_env("PAPER_OIDC_ISSUER", ""),
        oidc_client_id=_env("PAPER_OIDC_CLIENT_ID", ""),
        oidc_audience=_env("PAPER_OIDC_AUDIENCE", ""),
        oidc_scopes=_env("PAPER_OIDC_SCOPES", "openid profile email"),
        oidc_provider_name=_env("PAPER_OIDC_PROVIDER_NAME", "KBF SSO"),
        oidc_jwks_url=_env("PAPER_OIDC_JWKS_URL", ""),
        oidc_algorithms=_env("PAPER_OIDC_ALGORITHMS", "RS256"),
        session_secret=_env("PAPER_SESSION_SECRET", "paper-dev-secret-change-me"),
        session_ttl_s=int(_env("PAPER_SESSION_TTL_S", "86400")),
        session_cookie_name=_env("PAPER_SESSION_COOKIE_NAME", "paper_session"),
        session_cookie_secure=_env("PAPER_SESSION_COOKIE_SECURE", "false").lower() in {
            "1",
            "true",
            "yes",
        },
        storage_root=_env("PAPER_STORAGE_ROOT", "./data"),
        paperbanana_root=_env("PAPER_PAPERBANANA_ROOT", "/opt/PaperBanana"),
        paperbanana_python=_env("PAPER_PAPERBANANA_PYTHON", ""),
        paperbanana_candidates=int(_env("PAPER_PAPERBANANA_CANDIDATES", "1")),
    )
