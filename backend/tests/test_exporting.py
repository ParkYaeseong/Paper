from __future__ import annotations

import re
from pathlib import Path
import zipfile

from app.config import get_settings
from app.models import CitationSlot, DraftSection, EvidenceMatch, Project, ReferenceRecord
from app.services.exporting import run_export


def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    return " ".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml))


def test_run_export_normalizes_citation_variants_and_figure_placeholders(db_session_factory) -> None:
    with db_session_factory() as session:
        project = Project(
            owner_sub="user-1",
            owner_username="tester",
            title="protein_pipeline manuscript",
            objective="Describe an automated protein design pipeline.",
        )
        session.add(project)
        session.flush()

        slot_intro_1 = CitationSlot(
            project_id=project.id,
            section_key="introduction",
            slot_key="CIT_INTRODUCTION_1",
            claim_text="Protein design pipelines improve reproducibility.",
            context_text="Introduction",
            ordinal=1,
            status="supported",
        )
        slot_intro_2 = CitationSlot(
            project_id=project.id,
            section_key="introduction",
            slot_key="CIT_INTRODUCTION_2",
            claim_text="Protein design tools are often fragmented.",
            context_text="Introduction",
            ordinal=2,
            status="supported",
        )
        slot_conclusion = CitationSlot(
            project_id=project.id,
            section_key="conclusion",
            slot_key="CIT_CONCLUSION_1",
            claim_text="Expert review remains necessary.",
            context_text="Conclusion",
            ordinal=1,
            status="manual_review",
        )
        session.add_all([slot_intro_1, slot_intro_2, slot_conclusion])
        session.flush()

        ref_1 = ReferenceRecord(
            project_id=project.id,
            source="pubmed",
            external_id="PMID:1",
            title="Automated protein design workflows improve reproducibility",
            abstract="Protein design workflows improve reproducibility and reduce fragmentation.",
            authors_json=["Lee J", "Kim A"],
            venue="Synthetic Biology",
            year=2024,
            doi="10.1000/test-1",
            url="https://example.org/1",
            metadata_json={},
        )
        ref_2 = ReferenceRecord(
            project_id=project.id,
            source="openalex",
            external_id="W123",
            title="Integrated platforms reduce fragmentation in computational protein design",
            abstract="Integrated platforms reduce fragmentation across computational protein design tools.",
            authors_json=["Park Y"],
            venue="Bioinformatics",
            year=2023,
            doi="10.1000/test-2",
            url="https://example.org/2",
            metadata_json={},
        )
        session.add_all([ref_1, ref_2])
        session.flush()

        session.add_all(
            [
                EvidenceMatch(
                    project_id=project.id,
                    citation_slot_id=slot_intro_1.id,
                    queries_json=[],
                    candidate_reference_ids_json=[ref_1.id],
                    selected_reference_ids_json=[ref_1.id],
                    support_score=0.42,
                    status="supported",
                ),
                EvidenceMatch(
                    project_id=project.id,
                    citation_slot_id=slot_intro_2.id,
                    queries_json=[],
                    candidate_reference_ids_json=[ref_2.id],
                    selected_reference_ids_json=[ref_2.id],
                    support_score=0.31,
                    status="supported",
                ),
            ]
        )

        session.add_all(
            [
                DraftSection(
                    project_id=project.id,
                    section_key="introduction",
                    heading="Introduction",
                    version=1,
                    content=(
                        "## Introduction\n"
                        "Protein design workflows are often fragmented [CIT_INTRODUCTION_1, CIT_INTRODUCTION_2].\n\n"
                        "The platform consolidates orchestration `CIT_INTRODUCTION_1`.\n\n"
                        "[FIGURE_1: Overall protein_pipeline architecture and stage flow.]"
                    ),
                    status="drafted",
                ),
                DraftSection(
                    project_id=project.id,
                    section_key="conclusion",
                    heading="Conclusion",
                    version=1,
                    content="Expert review remains necessary CIT_CONCLUSION_1.",
                    status="drafted",
                ),
            ]
        )
        session.commit()

        bundle = run_export(session, project, get_settings())

        markdown = Path(bundle.manifest_json["markdown_path"]).read_text(encoding="utf-8")
        assert markdown.count("## Introduction") == 1
        assert "fragmented [1, 2]." in markdown
        assert "orchestration [1]." in markdown
        assert "Figure 1. Suggested insert: Overall protein_pipeline architecture and stage flow." in markdown
        assert "Expert review remains necessary [manual review]." in markdown
        assert "## References" in markdown
        assert "Automated protein design workflows improve reproducibility" in markdown

        docx_text = _docx_text(Path(bundle.manifest_json["docx_path"]))
        assert "Figure 1. Suggested insert: Overall protein_pipeline architecture and stage flow." in docx_text
        assert "Expert review remains necessary [manual review]." in docx_text
