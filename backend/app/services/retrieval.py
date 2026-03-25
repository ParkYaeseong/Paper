from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CitationSlot, EvidenceMatch, Project, ReferenceRecord


def _query_terms(text: str) -> list[str]:
    tokens = [token.strip(".,:;()[]").lower() for token in text.split()]
    keywords = [token for token in tokens if len(token) > 4]
    if not keywords:
        keywords = tokens[:5]
    return keywords[:6]


def build_queries(project: Project, claim_text: str) -> list[str]:
    joined_terms = " ".join(_query_terms(claim_text))
    title_terms = " ".join(_query_terms(project.title))
    return [
        claim_text,
        f"{joined_terms} {title_terms}".strip(),
    ]


def _joined_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return " ".join(chunk.strip() for chunk in node.itertext() if chunk and chunk.strip()).strip()


def _parse_pubmed_article_details(xml_text: str) -> dict[str, dict[str, Any]]:
    if not xml_text.strip():
        return {}
    root = ET.fromstring(xml_text)
    items: dict[str, dict[str, Any]] = {}
    for article in root.findall(".//PubmedArticle"):
        pubmed_id = _joined_text(article.find("./MedlineCitation/PMID"))
        if not pubmed_id:
            continue
        authors: list[str] = []
        for author in article.findall(".//AuthorList/Author"):
            collective_name = _joined_text(author.find("./CollectiveName"))
            if collective_name:
                authors.append(collective_name)
                continue
            last_name = _joined_text(author.find("./LastName"))
            initials = _joined_text(author.find("./Initials"))
            formatted = " ".join(part for part in [last_name, initials] if part).strip()
            if formatted:
                authors.append(formatted)

        year_text = (
            _joined_text(article.find(".//JournalIssue/PubDate/Year"))
            or _joined_text(article.find(".//ArticleDate/Year"))
            or _joined_text(article.find(".//PubDate/MedlineDate"))
        )
        year = int(year_text[:4]) if year_text[:4].isdigit() else None

        doi = ""
        for article_id in article.findall(".//ArticleIdList/ArticleId"):
            if str(article_id.attrib.get("IdType") or "").lower() == "doi":
                doi = _joined_text(article_id)
                if doi:
                    break

        abstract_parts = [_joined_text(node) for node in article.findall(".//Abstract/AbstractText")]
        items[pubmed_id] = {
            "title": _joined_text(article.find(".//ArticleTitle")),
            "abstract": " ".join(part for part in abstract_parts if part).strip(),
            "authors": authors,
            "venue": _joined_text(article.find(".//Journal/Title")),
            "year": year,
            "doi": doi,
        }
    return items


def search_pubmed(query: str, limit: int = 5) -> list[dict[str, Any]]:
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    search_response = requests.get(
        f"{base}/esearch.fcgi",
        params={"db": "pubmed", "retmode": "json", "retmax": limit, "term": query},
        timeout=20,
    )
    search_response.raise_for_status()
    ids = search_response.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    summary_response = requests.get(
        f"{base}/esummary.fcgi",
        params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)},
        timeout=20,
    )
    summary_response.raise_for_status()
    fetch_response = requests.get(
        f"{base}/efetch.fcgi",
        params={"db": "pubmed", "retmode": "xml", "id": ",".join(ids)},
        timeout=20,
    )
    fetch_response.raise_for_status()
    result = summary_response.json().get("result", {})
    details_by_id = _parse_pubmed_article_details(fetch_response.text)
    items: list[dict[str, Any]] = []
    for pubmed_id in ids:
        paper = result.get(pubmed_id) or {}
        details = details_by_id.get(pubmed_id) or {}
        authors = details.get("authors") or [
            str(author.get("name") or "").strip() for author in paper.get("authors") or [] if author.get("name")
        ]
        items.append(
            {
                "source": "pubmed",
                "external_id": f"PMID:{pubmed_id}",
                "title": str(details.get("title") or paper.get("title") or "").strip(),
                "abstract": str(details.get("abstract") or "").strip(),
                "authors": authors,
                "venue": str(details.get("venue") or paper.get("fulljournalname") or "").strip(),
                "year": details.get("year")
                or (
                    int(str(paper.get("pubdate") or "0")[:4] or 0)
                    if str(paper.get("pubdate") or "")[:4].isdigit()
                    else None
                ),
                "doi": str(details.get("doi") or "").strip(),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/",
            }
        )
    return items


def _reconstruct_openalex_abstract(inverted_index: dict[str, Any] | None) -> str:
    if not isinstance(inverted_index, dict):
        return ""
    positioned_tokens: list[tuple[int, str]] = []
    for token, positions in inverted_index.items():
        if not isinstance(positions, list):
            continue
        for position in positions:
            if isinstance(position, int):
                positioned_tokens.append((position, str(token)))
    if not positioned_tokens:
        return ""
    positioned_tokens.sort(key=lambda item: item[0])
    return " ".join(token for _, token in positioned_tokens).strip()


def search_openalex(query: str, limit: int = 5) -> list[dict[str, Any]]:
    response = requests.get(
        "https://api.openalex.org/works",
        params={"search": query, "per-page": limit},
        timeout=20,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    items: list[dict[str, Any]] = []
    for paper in results:
        authors = [
            str(author.get("author", {}).get("display_name") or "").strip()
            for author in paper.get("authorships") or []
            if author.get("author", {}).get("display_name")
        ]
        items.append(
            {
                "source": "openalex",
                "external_id": str(paper.get("id") or "").strip(),
                "title": str(paper.get("title") or "").strip(),
                "abstract": _reconstruct_openalex_abstract(paper.get("abstract_inverted_index")),
                "authors": authors,
                "venue": str(paper.get("primary_location", {}).get("source", {}).get("display_name") or "").strip(),
                "year": paper.get("publication_year"),
                "doi": str(paper.get("doi") or "").replace("https://doi.org/", ""),
                "url": str(paper.get("primary_location", {}).get("landing_page_url") or paper.get("id") or "").strip(),
            }
        )
    return items


def _reference_identity(record: dict[str, Any]) -> str:
    doi = str(record.get("doi") or "").strip().lower()
    if doi:
        return f"doi:{doi}"
    title = str(record.get("title") or "").strip().lower()
    return f"title:{title}"


def _get_or_create_reference(session: Session, project_id: str, record: dict[str, Any]) -> ReferenceRecord:
    identity = _reference_identity(record)
    existing = None
    if identity.startswith("doi:"):
        doi = identity[4:]
        existing = session.scalars(
            select(ReferenceRecord).where(ReferenceRecord.project_id == project_id, ReferenceRecord.doi.ilike(doi))
        ).first()
    else:
        title = identity[6:]
        existing = session.scalars(
            select(ReferenceRecord).where(ReferenceRecord.project_id == project_id, ReferenceRecord.title.ilike(title))
        ).first()
    if existing is not None:
        return existing
    reference = ReferenceRecord(
        project_id=project_id,
        source=str(record.get("source") or "external"),
        external_id=str(record.get("external_id") or ""),
        title=str(record.get("title") or ""),
        abstract=str(record.get("abstract") or ""),
        authors_json=list(record.get("authors") or []),
        venue=str(record.get("venue") or ""),
        year=record.get("year"),
        doi=str(record.get("doi") or ""),
        url=str(record.get("url") or ""),
        metadata_json={},
    )
    session.add(reference)
    session.flush()
    return reference


def run_retrieve(session: Session, project: Project) -> list[EvidenceMatch]:
    slots = list(session.scalars(select(CitationSlot).where(CitationSlot.project_id == project.id).order_by(CitationSlot.section_key, CitationSlot.ordinal)))
    matches: list[EvidenceMatch] = []
    for slot in slots:
        queries = build_queries(project, slot.claim_text)
        combined_records: list[dict[str, Any]] = []
        seen_identities: set[str] = set()
        for query in queries:
            for search_fn in (search_pubmed, search_openalex):
                try:
                    records = search_fn(query, limit=5)
                except Exception:
                    records = []
                for record in records:
                    identity = _reference_identity(record)
                    if identity in seen_identities:
                        continue
                    seen_identities.add(identity)
                    combined_records.append(record)
        candidate_ids: list[str] = []
        for record in combined_records:
            reference = _get_or_create_reference(session, project.id, record)
            candidate_ids.append(reference.id)

        match = session.scalars(
            select(EvidenceMatch).where(
                EvidenceMatch.project_id == project.id,
                EvidenceMatch.citation_slot_id == slot.id,
            )
        ).first()
        if match is None:
            match = EvidenceMatch(project_id=project.id, citation_slot_id=slot.id)
            session.add(match)
        match.queries_json = queries
        match.candidate_reference_ids_json = candidate_ids
        match.selected_reference_ids_json = []
        match.support_score = 0.0
        match.status = "retrieved" if candidate_ids else "manual_review"
        matches.append(match)

    session.commit()
    for match in matches:
        session.refresh(match)
    return matches
