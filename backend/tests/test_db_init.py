from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy import create_engine, inspect


def test_init_schema_creates_tables_without_prior_model_import(tmp_path):
    database_path = tmp_path / "runtime-init.db"
    env = os.environ.copy()
    env["PAPER_DATABASE_URL"] = f"sqlite:///{database_path}"
    backend_root = Path(__file__).resolve().parents[1]

    subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.db import init_schema; init_schema()",
        ],
        check=True,
        cwd=str(backend_root),
        env=env,
    )

    engine = create_engine(f"sqlite:///{database_path}")
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
