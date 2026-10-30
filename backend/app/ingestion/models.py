from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol


@dataclass(frozen=True)
class DocumentRef:
    source_id: str
    url: str
    catalog_year: int | None = None
    catalog_data: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


@dataclass
class FetchedDocument:
    """The legacy detail_html field carries snapshot bytes in detail_format."""

    ref: DocumentRef
    metadata: dict[str, Any]
    original: bytes
    detail_html: bytes
    original_url: str
    response_headers: dict[str, str]
    detail_format: str = "html"
    original_format: str = "pdf"
    related_documents: list[DocumentRef] = field(default_factory=list)


class Source(Protocol):
    name: str
    allowed_hosts: set[str]

    def reference(self, source_id: str) -> DocumentRef: ...

    def discover(self, client: Any, years: list[int] | None) -> Iterable[DocumentRef]: ...

    def fetch(self, client: Any, ref: DocumentRef) -> FetchedDocument: ...
