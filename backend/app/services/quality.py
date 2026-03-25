from __future__ import annotations

from collections import OrderedDict
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CitationSlot, DraftSection, EvidenceMatch, FigureSpec, Project, QualityReport, ReferenceRecord
from app.services.exporting import CITATION_TOKEN_RE, FIGURE_PLACEHOLDER_RE
from app.services.grounding import _support_score


REQUIRED_SECTION_KEYS = {"introduction", "methods", "results", "discussion", "limitations", "conclusion"}
GENERIC_RESULTS_RE = re.compile(r"\b(improves?|useful|practical utility|supports|helps|valuable|benefit)\b", re.IGNORECASE)
DIGIT_RE = re.compile(r"\d")


def _report_version(session: Session, project_id: str) -> int:
    version = session.scalar(select(func.max(QualityReport.version)).where(QualityReport.project_id == project_id))
    return int(version or 0) + 1


def latest_quality_report(session: Session, project_id: str) -> QualityReport | None:
    return session.scalars(
        select(QualityReport).where(QualityReport.project_id == project_id).order_by(QualityReport.version.desc())
    ).first()


def _latest_sections(session: Session, project_id: str) -> list[DraftSection]:
    sections = list(
        session.scalars(
            select(DraftSection).where(DraftSection.project_id == project_id).order_by(DraftSection.created_at)
        ).all()
    )
    latest: dict[str, DraftSection] = {}
    for section in sections:
        current = latest.get(section.section_key)
        if current is None or section.version > current.version:
            latest[section.section_key] = section
    return list(latest.values())


def _add_issue(bucket: list[dict[str, object]], code: str, message: str, **extra: object) -> None:
    issue = {"code": code, "message": message}
    issue.update({key: value for key, value in extra.items() if value is not None})
    bucket.append(issue)


def _recommended_actions(critical_issues: list[dict[str, object]], warnings: list[dict[str, object]]) -> list[str]:
    actions: list[str] = []
    codes = {issue["code"] for issue in critical_issues}
    warning_codes = {issue["code"] for issue in warnings}

    if {"unselected_reference", "manual_review_match", "unsupported_match", "irrelevant_reference"} & codes:
        actions.append("Review evidence matches and replace unsupported references before final export.")
    if {"unresolved_citation_token", "manual_review_marker"} & codes:
        actions.append("Resolve remaining citation placeholders and manual review markers in the draft.")
    if "unresolved_figure_placeholder" in codes:
        actions.append("Generate or select figure candidates for every figure placeholder.")
    if "missing_required_section" in codes:
        actions.append("Add the missing core manuscript sections before requesting a final export.")
    if {"generic_results_section", "missing_positioning_context"} & warning_codes:
        actions.append("Strengthen results and positioning with concrete artifacts, comparisons, and repository-specific details.")
    return list(OrderedDict.fromkeys(actions))


def run_quality_audit(session: Session, project: Project) -> QualityReport:
    critical_issues: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []

    sections = _latest_sections(session, project.id)
    section_map = {section.section_key: section for section in sections}
    slots = {
        slot.id: slot
        for slot in session.scalars(select(CitationSlot).where(CitationSlot.project_id == project.id)).all()
    }
    slots_by_key = {slot.slot_key: slot for slot in slots.values()}
    matches = {
        match.citation_slot_id: match
        for match in session.scalars(select(EvidenceMatch).where(EvidenceMatch.project_id == project.id)).all()
    }
    references = {
        reference.id: reference
        for reference in session.scalars(select(ReferenceRecord).where(ReferenceRecord.project_id == project.id)).all()
    }
    specs = {
        spec.figure_key: spec
        for spec in session.scalars(select(FigureSpec).where(FigureSpec.project_id == project.id)).all()
    }

    for section_key in sorted(REQUIRED_SECTION_KEYS - set(section_map)):
        _add_issue(
            critical_issues,
            "missing_required_section",
            f"The manuscript is missing the required section '{section_key}'.",
            section_key=section_key,
        )

    for section in sections:
        content = section.content or ""
        if "[manual review]" in content.lower():
            _add_issue(
                critical_issues,
                "manual_review_marker",
                "The draft still contains a manual review marker.",
                section_key=section.section_key,
            )
        for slot_key in CITATION_TOKEN_RE.findall(content):
            slot = slots_by_key.get(slot_key)
            match = None if slot is None else matches.get(slot.id)
            if slot is not None and match is not None and match.selected_reference_ids_json:
                continue
            _add_issue(
                critical_issues,
                "unresolved_citation_token",
                f"{slot_key} does not resolve to selected evidence in the draft.",
                section_key=section.section_key,
                slot_key=slot_key,
            )
        for match in FIGURE_PLACEHOLDER_RE.finditer(content):
            figure_number = int(match.group(1))
            figure_key = f"FIGURE_{figure_number}"
            spec = specs.get(figure_key)
            selected_asset = None if spec is None else next((asset for asset in spec.figure_assets if asset.selected), None)
            if selected_asset is None:
                _add_issue(
                    critical_issues,
                    "unresolved_figure_placeholder",
                    f"Figure {figure_number} does not have a selected generated asset.",
                    section_key=section.section_key,
                    figure_key=figure_key,
                )

    for slot in slots.values():
        match = matches.get(slot.id)
        if match is None or not match.selected_reference_ids_json:
            _add_issue(
                critical_issues,
                "unselected_reference",
                f"{slot.slot_key} does not have a selected supporting reference.",
                section_key=slot.section_key,
                slot_key=slot.slot_key,
            )
            continue
        if match.status in {"manual_review", "unsupported"}:
            _add_issue(
                critical_issues,
                f"{match.status}_match",
                f"{slot.slot_key} is still marked as {match.status}.",
                section_key=slot.section_key,
                slot_key=slot.slot_key,
            )
        elif match.status == "weak":
            _add_issue(
                warnings,
                "weak_evidence_match",
                f"{slot.slot_key} only has weak literature support.",
                section_key=slot.section_key,
                slot_key=slot.slot_key,
            )

        selected_reference = references.get(match.selected_reference_ids_json[0])
        if selected_reference is not None:
            support = _support_score(slot.claim_text, selected_reference)
            if support < 0.08:
                _add_issue(
                    critical_issues,
                    "irrelevant_reference",
                    f"The selected reference for {slot.slot_key} appears weakly related to the claim.",
                    section_key=slot.section_key,
                    slot_key=slot.slot_key,
                    reference_title=selected_reference.title,
                )

    results_section = section_map.get("results")
    if results_section is not None:
        results_text = FIGURE_PLACEHOLDER_RE.sub("", results_section.content)
        if not DIGIT_RE.search(results_text) and GENERIC_RESULTS_RE.search(results_text):
            _add_issue(
                warnings,
                "generic_results_section",
                "The results section reads generically and lacks concrete artifact-backed evidence.",
                section_key="results",
            )

    intro_text = (section_map.get("introduction").content if section_map.get("introduction") else "") or ""
    discussion_text = (section_map.get("discussion").content if section_map.get("discussion") else "") or ""
    related_text = f"{intro_text}\n{discussion_text}".lower()
    if not any(token in related_text for token in ("related work", "compared", "prior work", "existing tools")):
        _add_issue(
            warnings,
            "missing_positioning_context",
            "The manuscript needs clearer positioning against related work or existing systems.",
        )

    report = QualityReport(
        project_id=project.id,
        version=_report_version(session, project.id),
        critical_issues_json=critical_issues,
        warnings_json=warnings,
        recommended_actions_json=_recommended_actions(critical_issues, warnings),
        submission_ready=not critical_issues,
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return report
