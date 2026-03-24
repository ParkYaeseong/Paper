from sqlalchemy import create_engine, inspect

from app.db import Base
from app import models  # noqa: F401


def test_metadata_creates_expected_tables():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())

    assert {
        "projects",
        "artifacts",
        "dataset_profiles",
        "outlines",
        "draft_sections",
        "citation_slots",
        "reference_records",
        "evidence_matches",
        "review_decisions",
        "export_bundles",
        "job_runs",
    }.issubset(tables)
