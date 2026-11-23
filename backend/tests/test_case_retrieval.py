from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from opensearchpy.exceptions import NotFoundError
from pydantic import AnyHttpUrl, ValidationError

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.services.case_retrieval import MAX_DECISION_CHARS, fetch_case, search_cases
from backend.app.services.opensearch import opensearch_engine


@pytest.fixture
def court_index(monkeypatch):
    monkeypatch.setattr(settings, "CASE_CITATION_BASE_URL", AnyHttpUrl("https://api.example.org"))
    monkeypatch.setattr(settings, "OPENSEARCH_INDEX_PREFIX", "encuentra-test")
    monkeypatch.setattr(settings, "S3_PRESIGN_ON_SEARCH", True)
    monkeypatch.setattr(settings, "S3_PRESIGN_ON_QUERY", True)
    client = Mock()
    client.indices.exists_alias.return_value = True
    monkeypatch.setattr(opensearch_engine, "_get_client", lambda: client)
    monkeypatch.setattr(opensearch_engine, "_presign_key", Mock(side_effect=AssertionError("Unexpected presign")))
    monkeypatch.setattr(opensearch_engine, "_presign_by_id", Mock(side_effect=AssertionError("Unexpected S3 lookup")))
    return client


def test_search_fetch_and_citation_use_the_same_case(court_index):
    case_id = "A/ñ &1"
    doc = {"id": case_id, "title": "Fallo <A>", "case_year": 2024, "s3_file_key": "2024/A.PDF"}
    court_index.search.return_value = {"hits": {"hits": [
        {"_id": case_id, "_source": doc, "highlight": {"text": ["Fragmento de la resolución"]}},
    ]}}
    text = "Resolución <script>alert(1)</script>\n" + "x" * MAX_DECISION_CHARS
    court_index.get.return_value = {"_source": {**doc, "text": text}}

    hit, = search_cases("  audiencia  ", year=2024, limit=1)
    search = court_index.search.call_args.kwargs
    assert search["index"] == "encuentra-test-supreme_court"
    assert search["body"]["size"] == 1
    query = search["body"]["query"]["bool"]
    assert query["must"][0]["multi_match"]["query"] == "audiencia"
    assert {"term": {"case_year": 2024}} in query["filter"][0]["bool"]["should"]
    assert hit.snippet == "Fragmento de la resolución"
    assert hit.case_year == 2024

    decision = fetch_case(hit.id)
    court_index.get.assert_called_once_with(index="encuentra-test-supreme_court", id=case_id)
    assert decision.url == hit.url
    assert decision.text == text[:MAX_DECISION_CHARS]
    assert decision.truncated
    assert urlsplit(hit.url).netloc == "api.example.org"
    assert parse_qs(urlsplit(hit.url).query) == {"id": [case_id]}

    with TestClient(app) as client:
        response = client.get(hit.url)
        assert client.get("/ping").json() == {"status": "pong"}
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Fallo &lt;A&gt;" in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text
    assert "<script>" not in response.text
    assert "se muestra parcialmente" in response.text


def test_missing_and_disabled_citations(court_index, monkeypatch):
    court_index.search.return_value = {"hits": {"hits": []}}
    court_index.get.side_effect = NotFoundError(404, "not_found", {})

    assert search_cases("sin resultados") == []
    assert fetch_case("missing") is None
    with TestClient(app) as client:
        path = "/cases/supreme-court?id=missing"
        assert client.get(path).status_code == 404
        court_index.get.reset_mock()
        monkeypatch.setattr(settings, "CASE_CITATION_BASE_URL", None)
        assert client.get(path).status_code == 404
        court_index.get.assert_not_called()


@pytest.mark.parametrize("query, options", [("  ", {}), ("audiencia", {"limit": 21}), ("audiencia", {"year": 2101})])
def test_search_rejects_invalid_input(court_index, query, options):
    with pytest.raises(ValidationError):
        search_cases(query, **options)
    court_index.search.assert_not_called()


def test_existing_opensearch_callers_still_receive_download_urls(court_index):
    doc = {"id": "A", "title": "Resolución", "download_url": "https://example.org/A.pdf"}
    court_index.search.return_value = {"hits": {"hits": [{"_id": "A", "_source": doc}]}}
    court_index.get.return_value = {"_source": doc}

    assert opensearch_engine.search("resolución")[0]["download_url"] == doc["download_url"]
    assert opensearch_engine.get_document_by_id("supreme_court", "A")["download_url"] == doc["download_url"]
