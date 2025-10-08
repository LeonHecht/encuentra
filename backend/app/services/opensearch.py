"""OpenSearch-backed search service.

This module mirrors the interface of :mod:`backend.app.services.bm25`
so the rest of the application can switch between backends depending on
``settings.SEARCH_BACKEND``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from opensearchpy import OpenSearch, helpers
from opensearchpy.exceptions import NotFoundError

from ..core.config import settings


class OpenSearchSearch:
    def __init__(self) -> None:
        self._client: OpenSearch | None = None

    # ------------------------------------------------------------------
    # Client helpers
    # ------------------------------------------------------------------
    def _build_hosts(self) -> tuple[list[dict[str, Any]], bool | None]:
        hosts: list[dict[str, Any]] = []
        use_ssl: bool | None = None

        raw_hosts = [h.strip() for h in settings.OPENSEARCH_HOSTS.split(",") if h.strip()]
        if not raw_hosts:
            raise RuntimeError("OPENSEARCH_HOSTS is empty; cannot initialize OpenSearch client.")

        for raw in raw_hosts:
            if raw.startswith("http://") or raw.startswith("https://"):
                parsed = urlparse(raw)
                scheme = parsed.scheme or "http"
                host = parsed.hostname or "localhost"
                if parsed.port:
                    port = parsed.port
                else:
                    port = 443 if scheme == "https" else 80
                hosts.append({"host": host, "port": port})
                if use_ssl is None:
                    use_ssl = scheme == "https"
            else:
                if ":" in raw:
                    host_part, port_part = raw.split(":", 1)
                    try:
                        port = int(port_part)
                    except ValueError:
                        port = 9200
                    hosts.append({"host": host_part, "port": port})
                else:
                    hosts.append({"host": raw, "port": 9200})
        return hosts, use_ssl

    def _get_client(self) -> OpenSearch:
        if self._client is None:
            hosts, use_ssl = self._build_hosts()
            auth = None
            if settings.OPENSEARCH_USERNAME and settings.OPENSEARCH_PASSWORD:
                auth = (settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD)

            client_kwargs: dict[str, Any] = {
                "hosts": hosts,
                "http_compress": True,
                "timeout": settings.OPENSEARCH_TIMEOUT,
                "verify_certs": settings.OPENSEARCH_VERIFY_CERTS,
            }
            if use_ssl is not None:
                client_kwargs["use_ssl"] = use_ssl
            if auth:
                client_kwargs["http_auth"] = auth
            if settings.OPENSEARCH_CA_CERT:
                client_kwargs["ca_certs"] = settings.OPENSEARCH_CA_CERT

            self._client = OpenSearch(**client_kwargs)
        return self._client

    # ------------------------------------------------------------------
    # Index helpers
    # ------------------------------------------------------------------
    def _index_name(self, space: str) -> str:
        safe = space.replace("/", "__").replace(" ", "_").lower()
        safe = re.sub(r"[^a-z0-9_\-]+", "-", safe)
        return f"{settings.OPENSEARCH_INDEX_PREFIX}-{safe}"

    def _create_index_if_needed(self, client: OpenSearch, index_name: str) -> None:
        if client.indices.exists(index=index_name):
            return

        body = {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1,
                },
                "analysis": {
                    "analyzer": {
                        "spanish_default": {
                            "type": "standard",
                            "stopwords": "_spanish_",
                        }
                    }
                },
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "spanish_default",
                        "fields": {"raw": {"type": "keyword"}},
                    },
                    "text": {
                        "type": "text",
                        "analyzer": "spanish_default",
                    },
                    "space": {"type": "keyword"},
                    "download_url": {"type": "keyword"},
                }
            },
        }
        client.indices.create(index=index_name, body=body)

    def _resolve_download_url(self, doc_id: str) -> str | None:
        files_root = Path(settings.CORPUS_PATH) / "files"
        for ext in (".pdf", ".PDF", ".htm", ".html", ".HTML", ".docx", ".doc", ".txt"):
            candidate = files_root / f"{doc_id}{ext}"
            if candidate.exists():
                return f"/files/{candidate.name}"
        return None

    def _load_documents(self, space: str) -> list[dict[str, Any]]:
        documents: list[dict[str, Any]] = []

        if space == "supreme_court":
            jsonl_file = Path(settings.CORPUS_PATH) / "corpus.jsonl"
            if not jsonl_file.exists():
                print(f"[OpenSearch] corpus.jsonl not found for space '{space}'.")
                return []
            with jsonl_file.open(encoding="utf-8") as fh:
                for line in fh:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    doc_id = obj.get("id") or obj.get("doc_id")
                    if not doc_id:
                        continue
                    title = obj.get("title", "")
                    text = obj.get("text", "")
                    content = f"{title} {text}".strip()
                    documents.append(
                        {
                            "id": doc_id,
                            "title": title,
                            "text": content,
                            "space": space,
                            "download_url": self._resolve_download_url(doc_id),
                        }
                    )
        else:
            dir_path = Path(settings.DATA_UPLOAD) / space
            if not dir_path.exists():
                print(f"[OpenSearch] Upload directory '{dir_path}' missing for space '{space}'.")
                return []
            for file in dir_path.glob("**/*.txt"):
                try:
                    text = file.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = file.read_text(encoding="latin-1")
                documents.append(
                    {
                        "id": file.stem,
                        "title": file.stem,
                        "text": text,
                        "space": space,
                        "download_url": None,
                    }
                )

        return documents

    def _bulk_actions(self, index_name: str, docs: Iterable[dict[str, Any]]):
        for doc in docs:
            yield {
                "_op_type": "index",
                "_index": index_name,
                "_id": doc["id"],
                "_source": doc,
            }

    # ------------------------------------------------------------------
    # Public API (mirrors BM25Search)
    # ------------------------------------------------------------------
    def index(self, space: str = "supreme_court") -> None:
        client = self._get_client()
        index_name = self._index_name(space)

        documents = self._load_documents(space)
        if not documents:
            # Ensure stale data is removed if the space becomes empty.
            client.indices.delete(index=index_name, ignore=[400, 404])
            print(f"[OpenSearch] No documents to index for space '{space}'.")
            return

        # Drop the existing index to keep things in sync with the filesystem snapshot.
        client.indices.delete(index=index_name, ignore=[400, 404])
        self._create_index_if_needed(client, index_name)

        helpers.bulk(
            client,
            self._bulk_actions(index_name, documents),
            chunk_size=settings.OPENSEARCH_BULK_CHUNK_SIZE,
            refresh="wait_for",
        )
        print(f"[OpenSearch] Indexed {len(documents)} documents into '{index_name}'.")

    def has_space(self, space: str) -> bool:
        client = self._get_client()
        index_name = self._index_name(space)
        return bool(client.indices.exists(index=index_name))

    def search(self, query: str, top_k: int = 30, space: str = "supreme_court") -> list[dict[str, Any]]:
        client = self._get_client()
        index_name = self._index_name(space)
        if not client.indices.exists(index=index_name):
            print(f"[OpenSearch] Index '{index_name}' missing for space '{space}'.")
            return []

        body = {
            "size": top_k,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "text"],
                    "type": "best_fields",
                }
            },
            "highlight": {
                "fields": {
                    "text": {
                        "fragment_size": 200,
                        "number_of_fragments": 1,
                    }
                }
            },
        }

        response = client.search(index=index_name, body=body)
        hits: list[dict[str, Any]] = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            snippet = ""
            highlight = hit.get("highlight", {}).get("text")
            if highlight:
                snippet = " … ".join(highlight)
            else:
                text = source.get("text", "")
                snippet = " ".join(text.split()[:50])

            hits.append(
                {
                    "id": source.get("id") or hit.get("_id"),
                    "title": source.get("title", ""),
                    "score": float(hit.get("_score") or 0.0),
                    "snippet": snippet,
                    "download_url": source.get("download_url"),
                }
            )
        return hits

    def get_document_by_id(self, space: str, doc_id: str) -> dict[str, Any] | None:
        client = self._get_client()
        index_name = self._index_name(space)
        try:
            doc = client.get(index=index_name, id=doc_id)
        except NotFoundError:
            return None

        source = doc.get("_source", {})
        return {
            "id": doc_id,
            "title": source.get("title", ""),
            "text": source.get("text", ""),
            "download_url": source.get("download_url"),
        }


opensearch_engine = OpenSearchSearch()

