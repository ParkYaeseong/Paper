from __future__ import annotations

from typing import Any

import requests

from app.services.retrieval import search_openalex, search_pubmed


class _FakeResponse:
    def __init__(self, *, json_data: dict[str, Any] | None = None, text: str = "", status_code: int = 200) -> None:
        self._json_data = json_data or {}
        self.text = text
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")


def test_search_pubmed_fetches_abstracts(monkeypatch) -> None:
    def fake_get(url: str, params: dict[str, Any], timeout: int) -> _FakeResponse:
        if url.endswith("/esearch.fcgi"):
            return _FakeResponse(json_data={"esearchresult": {"idlist": ["123"]}})
        if url.endswith("/esummary.fcgi"):
            return _FakeResponse(
                json_data={
                    "result": {
                        "123": {
                            "title": "Protein design automation",
                            "fulljournalname": "Synthetic Biology Journal",
                            "pubdate": "2024 Jan",
                            "authors": [{"name": "Lee J"}],
                        }
                    }
                }
            )
        if url.endswith("/efetch.fcgi"):
            return _FakeResponse(
                text="""
                <PubmedArticleSet>
                  <PubmedArticle>
                    <MedlineCitation>
                      <PMID>123</PMID>
                      <Article>
                        <ArticleTitle>Protein design automation</ArticleTitle>
                        <Abstract>
                          <AbstractText>Computational protein design pipelines improve reproducibility.</AbstractText>
                        </Abstract>
                        <Journal>
                          <Title>Synthetic Biology Journal</Title>
                          <JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue>
                        </Journal>
                        <AuthorList>
                          <Author><LastName>Lee</LastName><Initials>J</Initials></Author>
                        </AuthorList>
                      </Article>
                    </MedlineCitation>
                    <PubmedData>
                      <ArticleIdList>
                        <ArticleId IdType="doi">10.1000/pubmed123</ArticleId>
                      </ArticleIdList>
                    </PubmedData>
                  </PubmedArticle>
                </PubmedArticleSet>
                """.strip()
            )
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("app.services.retrieval.requests.get", fake_get)

    items = search_pubmed("protein design reproducibility", limit=5)

    assert len(items) == 1
    assert items[0]["abstract"] == "Computational protein design pipelines improve reproducibility."
    assert items[0]["doi"] == "10.1000/pubmed123"
    assert items[0]["authors"] == ["Lee J"]


def test_search_openalex_reconstructs_inverted_index_abstract(monkeypatch) -> None:
    def fake_get(url: str, params: dict[str, Any], timeout: int) -> _FakeResponse:
        assert url == "https://api.openalex.org/works"
        return _FakeResponse(
            json_data={
                "results": [
                    {
                        "id": "https://openalex.org/W123",
                        "title": "Integrated protein design platforms",
                        "abstract_inverted_index": {
                            "Integrated": [0],
                            "protein": [1],
                            "design": [2],
                            "platforms": [3],
                            "improve": [4],
                            "reproducibility": [5],
                        },
                        "authorships": [{"author": {"display_name": "Park Y"}}],
                        "primary_location": {
                            "source": {"display_name": "Bioinformatics"},
                            "landing_page_url": "https://example.org/openalex/W123",
                        },
                        "publication_year": 2023,
                        "doi": "https://doi.org/10.1000/openalex123",
                    }
                ]
            }
        )

    monkeypatch.setattr("app.services.retrieval.requests.get", fake_get)

    items = search_openalex("protein design reproducibility", limit=5)

    assert len(items) == 1
    assert items[0]["abstract"] == "Integrated protein design platforms improve reproducibility"
    assert items[0]["doi"] == "10.1000/openalex123"
    assert items[0]["url"] == "https://example.org/openalex/W123"
