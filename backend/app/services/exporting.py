from __future__ import annotations

from collections import OrderedDict
import json
from pathlib import Path
import re
import uuid

from docx import Document
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import CitationSlot, DraftSection, EvidenceMatch, ExportBundle, Outline, Project, ReferenceRecord


PLACEHOLDER_RE = re.compile(r"\[(CIT_[A-Z0-9_]+)\]")


def _latest_sections(session: Session, project_id: str) -> list[DraftSection]:
    sections = list(session.scalars(select(DraftSection).where(DraftSection.project_id == project_id).order_by(DraftSection.created_at)).all())
    latest: dict[str, DraftSection] = {}
    for section in sections:
        current = latest.get(section.section_key)
        if current is None or section.version > current.version:
            latest[section.section_key] = section
    return list(latest.values())


def _latest_outline(session: Session, project_id: str) -> Outline | None:
    return session.scalars(select(Outline).where(Outline.project_id == project_id).order_by(Outline.version.desc())).first()


def _citation_numbering(session: Session, project_id: str) -> tuple[dict[str, int], dict[int, ReferenceRecord]]:
    slots = {
        slot.slot_key: slot
        for slot in session.scalars(select(CitationSlot).where(CitationSlot.project_id == project_id)).all()
    }
    matches = {
        match.citation_slot_id: match
        for match in session.scalars(select(EvidenceMatch).where(EvidenceMatch.project_id == project_id)).all()
    }
    sections = _latest_sections(session, project_id)
    ordered_refs: OrderedDict[str, ReferenceRecord] = OrderedDict()
    for section in sections:
        for slot_key in PLACEHOLDER_RE.findall(section.content):
            slot = slots.get(slot_key)
            if slot is None:
                continue
            match = matches.get(slot.id)
            if match is None:
                continue
            for ref_id in match.selected_reference_ids_json:
                if ref_id not in ordered_refs:
                    reference = session.get(ReferenceRecord, ref_id)
                    if reference is not None:
                        ordered_refs[ref_id] = reference
    slot_numbers: dict[str, int] = {}
    numbered_refs: dict[int, ReferenceRecord] = {}
    for index, (ref_id, reference) in enumerate(ordered_refs.items(), start=1):
        numbered_refs[index] = reference
        for slot in slots.values():
            match = matches.get(slot.id)
            if match and ref_id in match.selected_reference_ids_json and slot.slot_key not in slot_numbers:
                slot_numbers[slot.slot_key] = index
    return slot_numbers, numbered_refs


def _render_content(content: str, slot_numbers: dict[str, int]) -> str:
    def _replace(match: re.Match[str]) -> str:
        slot_key = match.group(1)
        number = slot_numbers.get(slot_key)
        if number is None:
            return "[manual review]"
        return f"[{number}]"

    return PLACEHOLDER_RE.sub(_replace, content)


def _render_reference_line(index: int, reference: ReferenceRecord) -> str:
    authors = ", ".join(reference.authors_json[:3]) if reference.authors_json else "Unknown author"
    year = f" ({reference.year})" if reference.year else ""
    venue = f". {reference.venue}" if reference.venue else ""
    doi = f". doi:{reference.doi}" if reference.doi else ""
    return f"[{index}] {authors}{year}. {reference.title}{venue}{doi}".strip()


def _render_bibtex_entry(reference: ReferenceRecord) -> str:
    key = (reference.doi or reference.external_id or reference.id).replace("/", "_").replace(":", "_")
    authors = " and ".join(reference.authors_json) if reference.authors_json else "Unknown"
    return (
        f"@article{{{key},\n"
        f"  title = {{{reference.title}}},\n"
        f"  author = {{{authors}}},\n"
        f"  journal = {{{reference.venue}}},\n"
        f"  year = {{{reference.year or ''}}},\n"
        f"  doi = {{{reference.doi}}},\n"
        f"}}"
    )


def run_export(session: Session, project: Project, settings: Settings) -> ExportBundle:
    output_root = Path(settings.storage_root).expanduser().resolve() / "exports" / project.id / str(uuid.uuid4())
    output_root.mkdir(parents=True, exist_ok=True)

    slot_numbers, numbered_refs = _citation_numbering(session, project.id)
    outline = _latest_outline(session, project.id)
    sections = _latest_sections(session, project.id)

    md_lines = [f"# {project.title}", ""]
    if outline is not None:
        md_lines.append(f"_Type: {outline.manuscript_type}_")
        md_lines.append("")
    for section in sections:
        md_lines.append(f"## {section.heading}")
        md_lines.append("")
        md_lines.append(_render_content(section.content, slot_numbers))
        md_lines.append("")
    md_lines.append("## References")
    md_lines.append("")
    for index, reference in numbered_refs.items():
        md_lines.append(_render_reference_line(index, reference))
    markdown = "\n".join(md_lines).strip() + "\n"

    bibtex = "\n\n".join(_render_bibtex_entry(reference) for reference in numbered_refs.values()).strip() + "\n"
    manuscript_json = {
        "project": {"id": project.id, "title": project.title, "objective": project.objective},
        "sections": [
            {
                "section_key": section.section_key,
                "heading": section.heading,
                "content": _render_content(section.content, slot_numbers),
            }
            for section in sections
        ],
        "references": [
            {
                "number": index,
                "title": reference.title,
                "doi": reference.doi,
                "authors": reference.authors_json,
            }
            for index, reference in numbered_refs.items()
        ],
    }

    md_path = output_root / "manuscript.md"
    md_path.write_text(markdown, encoding="utf-8")
    bib_path = output_root / "references.bib"
    bib_path.write_text(bibtex, encoding="utf-8")
    json_path = output_root / "manuscript.json"
    json_path.write_text(json.dumps(manuscript_json, indent=2), encoding="utf-8")

    document = Document()
    document.add_heading(project.title, level=0)
    for section in sections:
        document.add_heading(section.heading, level=1)
        document.add_paragraph(_render_content(section.content, slot_numbers))
    document.add_heading("References", level=1)
    for index, reference in numbered_refs.items():
        document.add_paragraph(_render_reference_line(index, reference))
    docx_path = output_root / "manuscript.docx"
    document.save(docx_path)

    bundle = ExportBundle(
        project_id=project.id,
        status="ready",
        manifest_json={
            "markdown_path": str(md_path),
            "bibtex_path": str(bib_path),
            "json_path": str(json_path),
            "docx_path": str(docx_path),
        },
    )
    session.add(bundle)
    session.commit()
    session.refresh(bundle)
    return bundle
