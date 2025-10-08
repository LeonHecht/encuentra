"""Helper module to select the active search backend."""

from __future__ import annotations

from ..core.config import settings
from .bm25 import bm25_engine

try:
    from .opensearch import opensearch_engine
except Exception as exc:  # pragma: no cover - defensive fallback when dependency missing
    opensearch_engine = None
    _opensearch_error = exc
else:
    _opensearch_error = None


def _select_engine():
    backend = (settings.SEARCH_BACKEND or "bm25").lower()
    if backend == "opensearch":
        if opensearch_engine is None:
            raise RuntimeError(
                "SEARCH_BACKEND=opensearch but the OpenSearch client could not be initialised"
                f": {_opensearch_error}"
            )
        return opensearch_engine
    return bm25_engine


search_engine = _select_engine()

