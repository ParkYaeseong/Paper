from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth import issue_session_cookie
from app.db import Base, get_db_session
from app.main import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("PAPER_OIDC_ISSUER", "https://sso.example.com/realms/kbf")
    monkeypatch.setenv("PAPER_OIDC_CLIENT_ID", "paper")
    monkeypatch.setenv("PAPER_SESSION_SECRET", "test-paper-secret")
    monkeypatch.setenv("PAPER_STORAGE_ROOT", str(tmp_path / "storage"))

    engine = create_engine(
        f"sqlite:///{tmp_path / 'paper-test.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    app = create_app()

    def override_get_db_session() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_cookie() -> str:
    user = {
        "sub": "user-1",
        "username": "tester",
        "email": "tester@example.com",
        "name": "Test User",
        "role": "user",
    }
    return issue_session_cookie("test-paper-secret", user, ttl_s=86400)


@pytest.fixture
def admin_cookie() -> str:
    user = {
        "sub": "admin-1",
        "username": "admin",
        "email": "admin@example.com",
        "name": "Admin User",
        "role": "admin",
    }
    return issue_session_cookie("test-paper-secret", user, ttl_s=86400)


@pytest.fixture
def other_user_cookie() -> str:
    user = {
        "sub": "user-2",
        "username": "other",
        "email": "other@example.com",
        "name": "Other User",
        "role": "user",
    }
    return issue_session_cookie("test-paper-secret", user, ttl_s=86400)
