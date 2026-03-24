from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CitationSlot, EvidenceMatch, ReferenceRecord


TOKEN_RE = re.compile(r"[a-zA-Z]{4,}")


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text)}


def _support_score(claim: str, reference: ReferenceRecord) -> float:
    claim_tokens = _tokens(claim)
    if not claim_tokens:
        return 0.0
    paper_tokens = _tokens(f"{reference.title} {reference.abstract}")
    if not paper_tokens:
        return 0.0
    overlap = claim_tokens & paper_tokens
    return round(len(overlap) / len(claim_tokens), 4)


def run_grounding(session: Session, project_id: str) -> list[EvidenceMatch]:
    slots = {
        slot.id: slot
        for slot in session.scalars(select(CitationSlot).where(CitationSlot.project_id == project_id)).all()
    }
    matches = list(session.scalars(select(EvidenceMatch).where(EvidenceMatch.project_id == project_id)).all())
    for match in matches:
        slot = slots.get(match.citation_slot_id)
        if slot is None:
            continue
        candidates = [
            session.get(ReferenceRecord, ref_id)
            for ref_id in match.candidate_reference_ids_json
            if session.get(ReferenceRecord, ref_id) is not None
        ]
        scored = sorted(
            ((reference.id, _support_score(slot.claim_text, reference)) for reference in candidates),
            key=lambda item: item[1],
            reverse=True,
        )
        if not scored:
            match.selected_reference_ids_json = []
            match.support_score = 0.0
            match.status = "unsupported"
            slot.status = "unsupported"
            continue
        top_score = scored[0][1]
        if top_score >= 0.2:
            selected = [ref_id for ref_id, score in scored[:2] if score >= 0.1]
            match.selected_reference_ids_json = selected
            match.support_score = top_score
            match.status = "supported"
            slot.status = "supported"
        elif top_score >= 0.08:
            match.selected_reference_ids_json = [scored[0][0]]
            match.support_score = top_score
            match.status = "weak"
            slot.status = "weak"
        else:
            match.selected_reference_ids_json = []
            match.support_score = top_score
            match.status = "manual_review"
            slot.status = "manual_review"
    session.commit()
    for match in matches:
        session.refresh(match)
    return matches
