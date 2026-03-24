from __future__ import annotations

from io import BytesIO


def test_pipeline_runs_end_to_end_with_fake_retrieval(client, auth_cookie: str, monkeypatch) -> None:
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
                "abstract": "Biofoundry automation improves throughput and reduces cycle time in strain engineering.",
                "authors": ["Doe J", "Kim A"],
                "venue": "Synthetic Biology Journal",
                "year": 2024,
                "doi": "10.1000/pubmed123",
                "url": "https://pubmed.ncbi.nlm.nih.gov/123/",
            }
        ],
    )
    monkeypatch.setattr("app.services.retrieval.search_openalex", lambda query, limit=5: [])

    for stage in ["ingest", "plan", "draft", "retrieve", "ground", "export"]:
        response = client.post(f"/api/projects/{project['id']}/pipeline/{stage}")
        assert response.status_code == 200, response.text
        assert response.json()["job"]["stage"] == stage
        assert response.json()["job"]["status"] == "succeeded"

    workspace = client.get(f"/api/projects/{project['id']}/workspace")

    assert workspace.status_code == 200
    body = workspace.json()
    assert body["dataset_profile"]["summary_json"]["dataset_summary"]["table_count"] == 1
    assert body["outline"]["manuscript_type"] == "original_article"
    assert len(body["draft_sections"]) >= 4
    assert len(body["citation_slots"]) >= 1
    assert len(body["evidence_matches"]) >= 1
    assert body["export_bundle"]["manifest_json"]["docx_path"].endswith(".docx")
