from __future__ import annotations

from io import BytesIO


def test_create_project(client, auth_cookie: str) -> None:
    client.cookies.set("paper_session", auth_cookie)

    response = client.post(
        "/api/projects",
        json={"title": "Funding analysis manuscript", "objective": "Analyze funding and performance outcomes."},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Funding analysis manuscript"
    assert body["owner_username"] == "tester"


def test_list_projects_only_returns_current_users_records(client, auth_cookie: str, other_user_cookie: str) -> None:
    client.cookies.set("paper_session", auth_cookie)
    first = client.post("/api/projects", json={"title": "Project A", "objective": "A"}).json()

    client.cookies.set("paper_session", other_user_cookie)
    client.post("/api/projects", json={"title": "Project B", "objective": "B"})

    client.cookies.set("paper_session", auth_cookie)
    response = client.get("/api/projects")

    assert response.status_code == 200
    projects = response.json()["items"]
    assert [item["id"] for item in projects] == [first["id"]]


def test_upload_artifact_to_owned_project(client, auth_cookie: str) -> None:
    client.cookies.set("paper_session", auth_cookie)
    project = client.post("/api/projects", json={"title": "Project A", "objective": "A"}).json()

    response = client.post(
        f"/api/projects/{project['id']}/artifacts",
        files={"files": ("results.csv", BytesIO(b"col1,col2\n1,2\n"), "text/csv")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["items"][0]["filename"] == "results.csv"
    assert payload["items"][0]["size_bytes"] > 0

    workspace = client.get(f"/api/projects/{project['id']}/workspace")

    assert workspace.status_code == 200
    body = workspace.json()
    assert len(body["artifacts"]) == 1
    assert body["artifacts"][0]["filename"] == "results.csv"


def test_reject_access_to_other_users_project(client, auth_cookie: str, other_user_cookie: str) -> None:
    client.cookies.set("paper_session", auth_cookie)
    project = client.post("/api/projects", json={"title": "Private project", "objective": "secret"}).json()

    client.cookies.set("paper_session", other_user_cookie)
    response = client.get(f"/api/projects/{project['id']}")

    assert response.status_code == 403
