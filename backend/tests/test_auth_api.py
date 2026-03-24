from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("PAPER_OIDC_ISSUER", "https://sso.example.com/realms/kbf")
    monkeypatch.setenv("PAPER_OIDC_CLIENT_ID", "paper")
    monkeypatch.setenv("PAPER_SESSION_SECRET", "test-paper-secret")
    return TestClient(create_app())


def test_oidc_config_exposes_provider_details(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    monkeypatch.setattr(
        "app.api.routes.auth.get_oidc_discovery",
        lambda settings: {
            "authorization_endpoint": "https://sso.example.com/auth",
            "end_session_endpoint": "https://sso.example.com/logout",
        },
    )

    response = client.get("/api/auth/oidc/config")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "enabled": True,
        "issuer": "https://sso.example.com/realms/kbf",
        "client_id": "paper",
        "scopes": "openid profile email",
        "provider_name": "KBF SSO",
        "authorization_endpoint": "https://sso.example.com/auth",
        "end_session_endpoint": "https://sso.example.com/logout",
        "account_url": "https://sso.example.com/realms/kbf/account/",
    }


def test_oidc_exchange_sets_session_cookie(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    monkeypatch.setattr(
        "app.api.routes.auth.exchange_oidc_code",
        lambda settings, *, code, redirect_uri, code_verifier=None: {"access_token": "access-token"},
    )
    monkeypatch.setattr(
        "app.api.routes.auth.verify_oidc_token",
        lambda token, settings: {
            "sub": "user-1",
            "preferred_username": "tester",
            "email": "tester@example.com",
            "name": "Test User",
            "azp": "paper",
            "iss": "https://sso.example.com/realms/kbf",
            "resource_access": {"paper": {"roles": ["paper-user"]}},
        },
    )

    response = client.post(
        "/api/auth/oidc/exchange",
        json={"code": "auth-code", "redirect_uri": "https://paper.example.com/callback"},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["user"]["username"] == "tester"
    assert response.cookies.get("paper_session")


def test_auth_me_requires_session(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
