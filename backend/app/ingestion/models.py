from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol


@dataclass(frozen=True)
class DocumentRef:
    source_id: str
    url: str
    catalog_year: int | None = None


@dataclass
class FetchedDocument:
    ref: DocumentRef
    metadata: dict[str, Any]
    original: bytes
    detail_html: bytes
    original_url: str
    response_headers: dict[str, str]


class Source(Protocol):
    name: str
    allowed_hosts: set[str]

    def reference(self, source_id: str) -> DocumentRef: ...

    def discover(self, client: Any, years: list[int] | None) -> Iterable[DocumentRef]: ...

    def fetch(self, client: Any, ref: DocumentRef) -> FetchedDocument: ...
