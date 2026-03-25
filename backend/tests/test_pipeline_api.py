from __future__ import annotations

from io import BytesIO
from pathlib import Path

def test_pipeline_runs_end_to_end_with_fake_retrieval(client, auth_cookie: str, monkeypatch, db_session_factory, tmp_path) -> None:
    client.cookies.set("paper_session", auth_cookie)
    project = client.post(
        "/api/projects",
        json={"title": "Biofoundry funding analysis", "objective": "Relate funding levels to throughput and yield."},
    ).json()

    upload = client.post(
        f"/api/projects/{project['id']}/artifacts",
        files={"files": ("results.csv", BytesIO(b"funding_amount,yield,cycle_time\n100,0.5,12\n200,0.7,8\n"), "text/csv")},
    )
    assert upload.status_code == 201

    monkeypatch.setattr(
        "app.services.retrieval.search_pubmed",
        lambda query, limit=5: [
            {
                "source": "pubmed",
                "external_id": "PMID:123",
                "title": "Biofoundry automation improves strain engineering throughput",
                "abstract": (
                    "Biofoundry automation improves throughput and reduces cycle time in strain engineering. "
                    "Resource allocation influences performance outcomes. Structured project artifacts can be normalized "
                    "into reproducible manuscript-ready profiles. Higher resource input accelerates DBTL cycle efficiency. "
                    "Grounded expert review remains necessary before publication."
                ),
                "authors": ["Doe J", "Kim A"],
                "venue": "Synthetic Biology Journal",
                "year": 2024,
                "doi": "10.1000/pubmed123",
                "url": "https://pubmed.ncbi.nlm.nih.gov/123/",
            }
        ],
    )
    monkeypatch.setattr("app.services.retrieval.search_openalex", lambda query, limit=5: [])
    monkeypatch.setattr("app.api.routes.workspace.enqueue_pipeline_job", lambda settings, job_id: job_id, raising=False)

    from app.jobs import process_pipeline_job

    response = client.post(f"/api/projects/{project['id']}/pipeline/run_all")
    assert response.status_code == 202, response.text
    job = response.json()["job"]
    assert job["stage"] == "run_all"
    assert job["status"] == "queued"
    process_pipeline_job(job["id"], session_factory=db_session_factory)

    for stage, payload in [("export", {"mode": "draft"}), ("export", {"mode": "final"})]:
        response = client.post(f"/api/projects/{project['id']}/pipeline/{stage}", json=payload)
        assert response.status_code == 202, response.text
        job = response.json()["job"]
        assert job["stage"] == stage
        assert job["status"] == "queued"
        process_pipeline_job(job["id"], session_factory=db_session_factory)

    workspace = client.get(f"/api/projects/{project['id']}/workspace")

    assert workspace.status_code == 200
    body = workspace.json()
    assert body["dataset_profile"]["summary_json"]["dataset_summary"]["table_count"] == 1
    assert body["outline"]["manuscript_type"] == "original_article"
    assert len(body["draft_sections"]) >= 4
    assert len(body["citation_slots"]) >= 1
    assert len(body["evidence_matches"]) >= 1
    assert body["quality_report"]["submission_ready"] is True
    assert len(body["figure_specs"]) >= 1
    assert body["figure_specs"][0]["method_section_content"]
    assert body["export_bundle"]["manifest_json"]["docx_path"].endswith(".docx")

    markdown = Path(body["export_bundle"]["manifest_json"]["markdown_path"]).read_text(encoding="utf-8")
    assert "## References" in markdown
    assert "Biofoundry automation improves strain engineering throughput" in markdown
    assert "Figure 1." in markdown or "Figure 2." in markdown
