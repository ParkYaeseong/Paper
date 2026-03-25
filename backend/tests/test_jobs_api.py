from __future__ import annotations

from io import BytesIO

from sqlalchemy import select

from app.models import Artifact, DatasetProfile, JobRun, Project


def _create_project(client, auth_cookie: str) -> dict:
    client.cookies.set("paper_session", auth_cookie)
    response = client.post(
        "/api/projects",
        json={"title": "Async manuscript", "objective": "Test queued pipeline execution."},
    )
    assert response.status_code == 201
    return response.json()


def test_enqueue_stage_returns_accepted_and_queued_job(client, auth_cookie: str, monkeypatch) -> None:
    project = _create_project(client, auth_cookie)

    upload = client.post(
        f"/api/projects/{project['id']}/artifacts",
        files={"files": ("results.csv", BytesIO(b"funding_amount,yield\n100,0.5\n"), "text/csv")},
    )
    assert upload.status_code == 201

    monkeypatch.setattr("app.api.routes.workspace.enqueue_pipeline_job", lambda settings, job_id: job_id, raising=False)

    response = client.post(f"/api/projects/{project['id']}/pipeline/ingest")

    assert response.status_code == 202
    body = response.json()
    assert body["job"]["stage"] == "ingest"
    assert body["job"]["status"] == "queued"


def test_duplicate_active_stage_job_is_rejected(client, auth_cookie: str, db_session_factory) -> None:
    project = _create_project(client, auth_cookie)

    with db_session_factory() as session:
        session.add(JobRun(project_id=project["id"], stage="ingest", status="queued"))
        session.commit()

    response = client.post(f"/api/projects/{project['id']}/pipeline/ingest")

    assert response.status_code == 409
    assert response.json()["detail"] == "An active job already exists for this stage"


def test_list_and_get_jobs_are_scoped_to_project(client, auth_cookie: str, db_session_factory) -> None:
    project = _create_project(client, auth_cookie)

    with db_session_factory() as session:
        first = JobRun(project_id=project["id"], stage="ingest", status="queued")
        second = JobRun(project_id=project["id"], stage="plan", status="failed", log_text="boom")
        session.add_all([first, second])
        session.commit()
        session.refresh(first)

    list_response = client.get(f"/api/projects/{project['id']}/jobs")
    detail_response = client.get(f"/api/projects/{project['id']}/jobs/{first.id}")

    assert list_response.status_code == 200
    assert len(list_response.json()["items"]) == 2
    assert detail_response.status_code == 200
    assert detail_response.json()["job"]["id"] == first.id


def test_worker_processes_queued_job_to_success(client, auth_cookie: str, db_session_factory) -> None:
    project = _create_project(client, auth_cookie)

    upload = client.post(
        f"/api/projects/{project['id']}/artifacts",
        files={"files": ("results.csv", BytesIO(b"funding_amount,yield\n100,0.5\n"), "text/csv")},
    )
    assert upload.status_code == 201

    with db_session_factory() as session:
        job = JobRun(project_id=project["id"], stage="ingest", status="queued")
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    from app.jobs import process_pipeline_job

    process_pipeline_job(job_id, session_factory=db_session_factory)

    with db_session_factory() as session:
        stored_job = session.get(JobRun, job_id)
        dataset_profile = session.scalars(
            select(DatasetProfile).where(DatasetProfile.project_id == project["id"])
        ).first()

    assert stored_job is not None
    assert stored_job.status == "succeeded"
    assert dataset_profile is not None


def test_worker_marks_job_failed_when_stage_raises(client, auth_cookie: str, db_session_factory) -> None:
    project = _create_project(client, auth_cookie)

    with db_session_factory() as session:
        job = JobRun(project_id=project["id"], stage="plan", status="queued")
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    from app.jobs import process_pipeline_job

    process_pipeline_job(job_id, session_factory=db_session_factory)

    with db_session_factory() as session:
        stored_job = session.get(JobRun, job_id)

    assert stored_job is not None
    assert stored_job.status == "failed"
    assert stored_job.log_text
