from __future__ import annotations

from app.models import CitationSlot, DraftSection, FigureSpec, Project, QualityReport
from app.services.quality import run_quality_audit


def test_run_quality_audit_flags_critical_issues_and_warnings(db_session_factory) -> None:
    with db_session_factory() as session:
        project = Project(
            owner_sub="user-1",
            owner_username="tester",
            title="protein_pipeline manuscript",
            objective="Describe a reproducible protein design workflow and its practical utility.",
        )
        session.add(project)
        session.flush()

        slot = CitationSlot(
            project_id=project.id,
            section_key="introduction",
            slot_key="CIT_INTRODUCTION_1",
            claim_text="Protein design systems benefit from reproducible orchestration.",
            context_text="Introduction",
            ordinal=1,
            status="manual_review",
        )
        session.add(slot)

        session.add_all(
            [
                DraftSection(
                    project_id=project.id,
                    section_key="introduction",
                    heading="Introduction",
                    version=1,
                    content=(
                        "Protein design workflows remain fragmented [manual review].\n\n"
                        "Reproducible orchestration is important CIT_INTRODUCTION_1."
                    ),
                    status="drafted",
                ),
                DraftSection(
                    project_id=project.id,
                    section_key="results",
                    heading="Results",
                    version=1,
                    content=(
                        "The system improves practical utility across use cases.\n\n"
                        "[FIGURE_1: Overall system architecture and staged workflow.]"
                    ),
                    status="drafted",
                ),
            ]
        )
        session.commit()

        report = run_quality_audit(session, project)

        assert isinstance(report, QualityReport)
        assert report.submission_ready is False
        critical_codes = {item["code"] for item in report.critical_issues_json}
        assert "manual_review_marker" in critical_codes
        assert "unresolved_citation_token" in critical_codes
        assert "unresolved_figure_placeholder" in critical_codes
        warning_codes = {item["code"] for item in report.warnings_json}
        assert "generic_results_section" in warning_codes
        assert report.recommended_actions_json


def test_run_quality_audit_accepts_prepared_figure_handoff_without_assets(db_session_factory) -> None:
    with db_session_factory() as session:
        project = Project(
            owner_sub="user-1",
            owner_username="tester",
            title="protein_pipeline manuscript",
            objective="Describe a reproducible protein design workflow and its practical utility.",
        )
        session.add(project)
        session.flush()

        session.add_all(
            [
                DraftSection(
                    project_id=project.id,
                    section_key="introduction",
                    heading="Introduction",
                    version=1,
                    content="Compared with prior work, this workflow keeps orchestration and review in one interface.",
                    status="drafted",
                ),
                DraftSection(
                    project_id=project.id,
                    section_key="methods",
                    heading="Methods",
                    version=1,
                    content=(
                        "The workflow combines upload, staged execution, and review.\n\n"
                        "[FIGURE_1: Overall system architecture and staged workflow.]"
                    ),
                    status="drafted",
                ),
                DraftSection(
                    project_id=project.id,
                    section_key="results",
                    heading="Results",
                    version=1,
                    content="We observed 12 successful runs across the staged workflow.",
                    status="drafted",
                ),
                DraftSection(
                    project_id=project.id,
                    section_key="discussion",
                    heading="Discussion",
                    version=1,
                    content="Compared with prior work, this system reduces handoff overhead during review.",
                    status="drafted",
                ),
                DraftSection(
                    project_id=project.id,
                    section_key="limitations",
                    heading="Limitations",
                    version=1,
                    content="The workflow still requires expert validation before submission.",
                    status="drafted",
                ),
                DraftSection(
                    project_id=project.id,
                    section_key="conclusion",
                    heading="Conclusion",
                    version=1,
                    content="The interface prepares review-ready outputs for manuscript assembly.",
                    status="drafted",
                ),
                FigureSpec(
                    project_id=project.id,
                    section_key="methods",
                    figure_key="FIGURE_1",
                    figure_number=1,
                    caption_draft="Overall system architecture and staged workflow.",
                    source_excerpt="The workflow combines upload, staged execution, and review.",
                    visual_intent="### Methods\n\nThe workflow combines upload, staged execution, and review.",
                    status="prepared",
                ),
            ]
        )
        session.commit()

        report = run_quality_audit(session, project)

        assert isinstance(report, QualityReport)
        assert report.submission_ready is True
        critical_codes = {item["code"] for item in report.critical_issues_json}
        assert "unresolved_figure_placeholder" not in critical_codes
