import json
from types import SimpleNamespace

import pytest

from backend.app.api.v1.endpoints import search as search_ep
from backend.app.services import case_metadata
from backend.app.services.auth import UserData


def _user() -> UserData:
    return UserData(user_id="user-1", username="test@example.com", spaces=["personal"])


def test_search_attaches_ready_metadata(monkeypatch):
    monkeypatch.setattr(search_ep, "get_accessible_spaces", lambda user: ["supreme_court"])
    monkeypatch.setattr(search_ep.search_engine, "has_space", lambda space: True)
    monkeypatch.setattr(
        search_ep.search_engine,
        "search",
        lambda q, top_k, space: [
            {
                "id": "539-2024",
                "title": "539-2024",
                "case_year": 2025,
                "score": 1.0,
                "snippet": "texto",
                "download_url": "https://example.com/doc.pdf",
            }
        ],
    )
    monkeypatch.setattr(
        search_ep.case_metadata,
        "get_metadata_rows",
        lambda space, doc_ids: {
            "539-2024": {
                "doc_id": "539-2024",
                "status": "ready",
                "metadata": {"generated_title": "Titulo juridico"},
            }
        },
    )
    monkeypatch.setattr(search_ep.case_metadata, "upsert_pending", lambda *args, **kwargs: False)

    response = search_ep.search(q="libertad", top_k=1, space="supreme_court", user=_user())

    assert response.results[0].metadata_status == "ready"
    assert response.results[0].metadata == {"generated_title": "Titulo juridico"}


def test_search_enqueues_missing_metadata(monkeypatch):
    enqueued = []
    monkeypatch.setattr(search_ep.settings, "CASE_METADATA_AUTO_ENRICH", True)
    monkeypatch.setattr(search_ep, "get_accessible_spaces", lambda user: ["supreme_court"])
    monkeypatch.setattr(search_ep.search_engine, "has_space", lambda space: True)
    monkeypatch.setattr(
        search_ep.search_engine,
        "search",
        lambda q, top_k, space: [
            {
                "id": "A1",
                "title": "A1",
                "score": 1.0,
                "snippet": "snippet-1",
                "download_url": None,
            },
            {
                "id": "A2",
                "title": "A2",
                "score": 0.9,
                "snippet": "snippet-2",
                "download_url": None,
            },
        ],
    )
    monkeypatch.setattr(search_ep.case_metadata, "get_metadata_rows", lambda space, doc_ids: {})
    monkeypatch.setattr(search_ep.case_metadata, "upsert_pending", lambda *args, **kwargs: True)
    monkeypatch.setattr(search_ep.case_metadata, "enrich_case_metadata", lambda *args: enqueued.append(args))

    class FakeBackgroundTasks:
        def add_task(self, fn, *args):
            fn(*args)

    response = search_ep.search(
        q="hurto",
        top_k=2,
        space="supreme_court",
        background_tasks=FakeBackgroundTasks(),
        user=_user(),
    )

    assert [result.metadata_status for result in response.results] == ["pending", "pending"]
    assert enqueued == [("supreme_court", "A1", "hurto", "snippet-1"), ("supreme_court", "A2", "hurto", "snippet-2")]


def test_metadata_endpoint_rejects_inaccessible_space(monkeypatch):
    monkeypatch.setattr(search_ep, "get_accessible_spaces", lambda user: ["supreme_court"])

    with pytest.raises(search_ep.HTTPException) as exc:
        search_ep.get_case_metadata(space="private", doc_id="A1", user=_user())

    assert exc.value.status_code == 403


def test_extract_metadata_with_openai_validates_structured_json(monkeypatch):
    payload = {
        "generated_title": "Habeas corpus sobre detencion provisional",
        "court_chamber": "Sala de lo Constitucional",
        "resolution_type": "Habeas corpus",
        "outcome": "Improcedente",
        "parties": {
            "actors": [],
            "favored_parties": ["NAAR"],
            "defendants_or_authorities": ["Juez"],
            "other_relevant_parties": [],
        },
        "legal_issue_summary": "Resumen",
        "key_legal_provisions": [],
        "relevant_dates": [],
        "legal_area_tags": ["habeas corpus"],
        "legal_questions": ["Procedencia del habeas corpus"],
        "confidence": {"overall": 0.9, "notes": None},
    }

    class FakeResponses:
        def create(self, **kwargs):
            assert kwargs["text"]["format"]["type"] == "json_schema"
            assert kwargs["text"]["format"]["strict"] is True
            return SimpleNamespace(output_text=json.dumps(payload))

    monkeypatch.setattr(case_metadata, "_get_openai_client", lambda: SimpleNamespace(responses=FakeResponses()))

    result = case_metadata.extract_metadata_with_openai(
        query="libertad",
        doc_id="539-2024",
        case_year=2025,
        matched_snippet="snippet",
        full_document_text="documento completo",
    )

    assert result.generated_title == payload["generated_title"]
    assert result.confidence.overall == 0.9


def test_enrich_case_metadata_marks_failed(monkeypatch):
    writes = []
    monkeypatch.setattr(case_metadata, "get_metadata_row", lambda space, doc_id: None)
    monkeypatch.setattr(case_metadata.search_engine, "get_document_by_id", lambda space, doc_id: {"text": "texto"})
    monkeypatch.setattr(case_metadata, "extract_metadata_with_openai", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    class FakeTable:
        def upsert(self, payload, on_conflict=None):
            writes.append(payload)
            return self

        def execute(self):
            return SimpleNamespace(data=[])

    monkeypatch.setattr(case_metadata, "get_supabase", lambda: SimpleNamespace(table=lambda name: FakeTable()))

    case_metadata.enrich_case_metadata("supreme_court", "A1")

    assert writes[0]["status"] == "failed"
    assert "boom" in writes[0]["error"]
