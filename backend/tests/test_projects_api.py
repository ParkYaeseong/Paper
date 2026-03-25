from __future__ import annotations

from io import BytesIO
from pathlib import Path


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
        data={"roles": "results_table"},
        files={"files": ("results.csv", BytesIO(b"col1,col2\n1,2\n"), "text/csv")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["items"][0]["filename"] == "results.csv"
    assert payload["items"][0]["size_bytes"] > 0
    assert payload["items"][0]["role"] == "results_table"
    assert payload["items"][0]["metadata_json"]["role"] == "results_table"

    workspace = client.get(f"/api/projects/{project['id']}/workspace")

    assert workspace.status_code == 200
    body = workspace.json()
    assert len(body["artifacts"]) == 1
    assert body["artifacts"][0]["filename"] == "results.csv"
    assert body["artifacts"][0]["role"] == "results_table"


def test_update_artifact_role_marks_new_role_in_workspace(client, auth_cookie: str) -> None:
    client.cookies.set("paper_session", auth_cookie)
    project = client.post("/api/projects", json={"title": "Project A", "objective": "A"}).json()

    upload = client.post(
        f"/api/projects/{project['id']}/artifacts",
        data={"roles": "supporting_doc"},
        files={"files": ("notes.md", BytesIO(b"# Notes\nInitial content\n"), "text/markdown")},
    )
    assert upload.status_code == 201
    artifact = upload.json()["items"][0]
    assert artifact["role"] == "supporting_doc"

    update = client.patch(
        f"/api/projects/{project['id']}/artifacts/{artifact['id']}",
        json={"role": "narrative_brief"},
    )

    assert update.status_code == 200
    updated = update.json()
    assert updated["role"] == "narrative_brief"
    assert updated["metadata_json"]["role"] == "narrative_brief"

    workspace = client.get(f"/api/projects/{project['id']}/workspace")
    assert workspace.status_code == 200
    assert workspace.json()["artifacts"][0]["role"] == "narrative_brief"


def test_delete_artifact_removes_file_and_workspace_entry(client, auth_cookie: str) -> None:
    client.cookies.set("paper_session", auth_cookie)
    project = client.post("/api/projects", json={"title": "Project A", "objective": "A"}).json()

    upload = client.post(
        f"/api/projects/{project['id']}/artifacts",
        files={"files": ("results.csv", BytesIO(b"col1,col2\n1,2\n"), "text/csv")},
    )
    artifact = upload.json()["items"][0]

    stored_path = Path(artifact["storage_path"])
    assert stored_path.exists()

    response = client.delete(f"/api/projects/{project['id']}/artifacts/{artifact['id']}")

    assert response.status_code == 204
    assert not stored_path.exists()

    workspace = client.get(f"/api/projects/{project['id']}/workspace")

    assert workspace.status_code == 200
    assert workspace.json()["artifacts"] == []


def test_uploading_same_filename_twice_keeps_distinct_storage_paths(client, auth_cookie: str) -> None:
    client.cookies.set("paper_session", auth_cookie)
    project = client.post("/api/projects", json={"title": "Project A", "objective": "A"}).json()

    first = client.post(
        f"/api/projects/{project['id']}/artifacts",
        files={"files": ("results.csv", BytesIO(b"col1,col2\n1,2\n"), "text/csv")},
    )
    second = client.post(
        f"/api/projects/{project['id']}/artifacts",
        files={"files": ("results.csv", BytesIO(b"col1,col2\n3,4\n"), "text/csv")},
    )

    first_path = first.json()["items"][0]["storage_path"]
    second_path = second.json()["items"][0]["storage_path"]

    assert first_path != second_path


def test_delete_project_removes_storage_and_records(client, auth_cookie: str) -> None:
    client.cookies.set("paper_session", auth_cookie)
    project = client.post("/api/projects", json={"title": "Project A", "objective": "A"}).json()

    upload = client.post(
        f"/api/projects/{project['id']}/artifacts",
        files={"files": ("results.csv", BytesIO(b"col1,col2\n1,2\n"), "text/csv")},
    )
    artifact = upload.json()["items"][0]
    project_root = Path(artifact["storage_path"]).parents[1]

    assert project_root.exists()

    response = client.delete(f"/api/projects/{project['id']}")

    assert response.status_code == 204
    assert not project_root.exists()

    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    assert list_response.json()["items"] == []

    project_response = client.get(f"/api/projects/{project['id']}")
    assert project_response.status_code == 404


def test_reject_access_to_other_users_project(client, auth_cookie: str, other_user_cookie: str) -> None:
    client.cookies.set("paper_session", auth_cookie)
    project = client.post("/api/projects", json={"title": "Private project", "objective": "secret"}).json()

    client.cookies.set("paper_session", other_user_cookie)
    response = client.get(f"/api/projects/{project['id']}")

    assert response.status_code == 403
