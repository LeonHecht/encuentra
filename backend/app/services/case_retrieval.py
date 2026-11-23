"""Read-only retrieval for citations to Supreme Court decisions."""

from typing import Annotated
from urllib.parse import urlencode, urljoin

from pydantic import BaseModel, Field, StringConstraints, validate_call

from ..core.config import settings
from .opensearch import opensearch_engine

CASE_CITATION_PATH = "/cases/supreme-court"
MAX_CASE_ID_LENGTH = 512
MAX_DECISION_CHARS = 12_000

_COURT_SPACE = "supreme_court"


class CaseCitation(BaseModel):
    id: str
    title: str
    case_year: int | None
    url: str


class CaseSearchHit(CaseCitation):
    snippet: str


class CaseDecision(CaseCitation):
    text: str
    truncated: bool


def _citation_page_url() -> str:
    if settings.CASE_CITATION_BASE_URL is None:
        raise RuntimeError("Set CASE_CITATION_BASE_URL to enable Supreme Court citations.")
    return urljoin(str(settings.CASE_CITATION_BASE_URL), CASE_CITATION_PATH)


def _citation_fields(doc: dict, page_url: str) -> dict:
    case_id = doc["id"]
    return {
        "id": case_id,
        "title": doc.get("title") or case_id,
        "case_year": doc.get("case_year"),
        "url": f"{page_url}?{urlencode({'id': case_id})}",
    }


@validate_call
def search_cases(
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)],
    *,
    year: Annotated[int, Field(ge=1800, le=2100)] | None = None,
    limit: Annotated[int, Field(ge=1, le=20)] = 5,
) -> list[CaseSearchHit]:
    page_url = _citation_page_url()
    hits = opensearch_engine.search(
        query,
        top_k=limit,
        space=_COURT_SPACE,
        year=year,
        include_download_url=False,
    )
    return [
        CaseSearchHit(**_citation_fields(hit, page_url), snippet=(hit.get("snippet") or "")[:500])
        for hit in hits
    ]


@validate_call
def fetch_case(case_id: Annotated[str, Field(min_length=1, max_length=MAX_CASE_ID_LENGTH)]) -> CaseDecision | None:
    page_url = _citation_page_url()
    doc = opensearch_engine.get_document_by_id(_COURT_SPACE, case_id, include_download_url=False)
    if doc is None:
        return None

    text = doc.get("text") or ""
    return CaseDecision(
        **_citation_fields(doc, page_url),
        text=text[:MAX_DECISION_CHARS],
        truncated=len(text) > MAX_DECISION_CHARS,
    )
