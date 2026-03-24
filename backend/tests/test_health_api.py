from fastapi.testclient import TestClient

from app.main import create_app


def test_healthz_returns_application_status():
    client = TestClient(create_app())

    response = client.get("/api/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "service": "paper-api",
        "status": "healthy",
    }
