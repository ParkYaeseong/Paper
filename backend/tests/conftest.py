from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth import issue_session_cookie
from app.db import Base, get_db_session
from app.main import create_app


@pytest.fixture(autouse=True)
def disable_live_llm(monkeypatch: pytest.MonkeyPatch):
    from app.services import llm

    monkeypatch.setattr(llm, "OPENAI_API_KEY", "", raising=False)
    monkeypatch.setattr(llm, "GEMINI_API_KEY", "", raising=False)


@pytest.fixture
def testing_session_factory(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("PAPER_OIDC_ISSUER", "https://sso.example.com/realms/kbf")
    monkeypatch.setenv("PAPER_OIDC_CLIENT_ID", "paper")
    monkeypatch.setenv("PAPER_SESSION_SECRET", "test-paper-secret")
    monkeypatch.setenv("PAPER_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("PAPER_REDIS_URL", "redis://localhost:6379/9")

    engine = create_engine(
        f"sqlite:///{tmp_path / 'paper-test.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    return TestingSessionLocal


@pytest.fixture
def app(testing_session_factory):
    app = create_app()

    def override_get_db_session() -> Generator[Session, None, None]:
        session = testing_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    return app


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session_factory(testing_session_factory):
    return testing_session_factory


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
