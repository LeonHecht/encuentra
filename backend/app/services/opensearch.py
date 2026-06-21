"""OpenSearch-backed search service.

This module mirrors the interface of :mod:`backend.app.services.bm25`
so the rest of the application can switch between backends depending on
``settings.SEARCH_BACKEND``.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from opensearchpy import OpenSearch, helpers
from opensearchpy import AWSV4SignerAuth, RequestsHttpConnection
from opensearchpy.exceptions import NotFoundError

# Optional S3 support (used when S3_* settings are configured)
try:  # lazy optional dependency
    import boto3  # type: ignore
    from botocore.exceptions import ClientError  # type: ignore
except Exception:  # pragma: no cover - optional
    boto3 = None
    ClientError = Exception

from ..core.config import settings


class OpenSearchSearch:
    def __init__(self) -> None:
        self._client: OpenSearch | None = None
        self._s3_client = None

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

            client_kwargs: dict[str, Any] = {
                "hosts": hosts,
                "http_compress": True,
                "timeout": settings.OPENSEARCH_TIMEOUT,
                "verify_certs": settings.OPENSEARCH_VERIFY_CERTS,
            }

            use_sigv4 = self._uses_sigv4()
            aws_region = getattr(settings, "OPENSEARCH_AWS_REGION", None)

            # --- Branch 1: AWS-managed OpenSearch / Serverless via IAM + SigV4 ---
            if use_sigv4:
                if boto3 is None:
                    raise RuntimeError(
                        "boto3 is required for AWS OpenSearch IAM auth but is not installed."
                    )
                if not aws_region:
                    raise RuntimeError(
                        "OPENSEARCH_SIGV4=true requires OPENSEARCH_AWS_REGION to be set."
                    )

                service = getattr(settings, "OPENSEARCH_AWS_SERVICE", "aoss")

                session = boto3.Session()
                credentials = session.get_credentials()
                if credentials is None:
                    raise RuntimeError("No AWS credentials available for OpenSearch IAM auth.")

                auth = AWSV4SignerAuth(credentials, aws_region, service)

                client_kwargs.update(
                    {
                        "http_auth": auth,
                        "use_ssl": True,
                        "verify_certs": True,
                        "connection_class": RequestsHttpConnection,
                    }
                )

            # --- Branch 2: Local / self-hosted clusters, including Docker on EC2 ---
            else:
                auth = None
                if settings.OPENSEARCH_USERNAME and settings.OPENSEARCH_PASSWORD:
                    auth = (settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD)

                if auth:
                    client_kwargs["http_auth"] = auth

                if use_ssl is not None:
                    client_kwargs["use_ssl"] = use_ssl
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

        # Base index settings, used for both self-hosted clusters and AOSS.
        index_settings: dict[str, Any] = {}

        # Only set shards/replicas when NOT on Serverless.
        if not self._is_serverless():
            index_settings.update(
                {
                    "number_of_shards": 1,
                    "number_of_replicas": 1,
                }
            )

        body = {
            "settings": {
                "index": index_settings,
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
                    "s3_text_key": {"type": "keyword"},
                    "s3_text_etag": {"type": "keyword"},
                    "s3_last_modified": {"type": "date"},
                    "indexed_at": {"type": "date"},
                }
            },
        }

        client.indices.create(index=index_name, body=body)

    def _resolve_download_url(self, doc_id: str) -> str | None:
        # Prefer S3 presigned URL if configured and presigning during indexing is enabled
        if (
            getattr(settings, "S3_BUCKET", None)
            and getattr(settings, "S3_FILES_PREFIX", None)
            and getattr(settings, "S3_PRESIGN_ON_INDEX", False)
        ):
            url = self._presign_by_id(doc_id)
            if url:
                return url

        # Filesystem fallback (dev/local)
        files_root = Path(settings.CORPUS_PATH) / "files"
        for ext in (".pdf", ".PDF", ".htm", ".html", ".HTML", ".docx", ".doc", ".txt"):
            candidate = files_root / f"{doc_id}{ext}"
            if candidate.exists():
                return f"/files/{candidate.name}"
        return None

    def _presign_by_id(self, doc_id: str) -> str | None:
        """Attempt to generate a presigned S3 URL for a given document id.
        Tries a set of known extensions and returns the first existing object's URL.
        """
        if boto3 is None:
            return None
        bucket = getattr(settings, "S3_BUCKET", None)
        prefix_raw = getattr(settings, "S3_FILES_PREFIX", None)
        if not bucket or not prefix_raw:
            return None
        try:
            client = self._get_s3_client()
            prefix = str(prefix_raw).rstrip("/") + "/"
            exts = (".pdf", ".PDF", ".htm", ".html", ".HTML", ".docx", ".doc", ".txt")

            # 1) Fast path: try keys without any year/extra folders,
            #    i.e. <prefix><doc_id><ext>
            for ext in exts:
                key = f"{prefix}{doc_id}{ext}"
                try:
                    client.head_object(Bucket=bucket, Key=key)
                except ClientError:
                    continue
                try:
                    return client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": bucket, "Key": key},
                        ExpiresIn=int(getattr(settings, "S3_URL_TTL", 604800)),
                    )
                except Exception:
                    return None

            # 2) Fallback: handle layouts like "year/doc_id.ext" where doc_id
            #    itself does not contain the year. We scan under the configured
            #    prefix and look for any key that ends with "/<doc_id><ext>".
            paginator = client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    k = obj.get("Key", "")
                    for ext in exts:
                        if k.endswith(f"/{doc_id}{ext}"):
                            try:
                                return client.generate_presigned_url(
                                    "get_object",
                                    Params={"Bucket": bucket, "Key": k},
                                    ExpiresIn=int(getattr(settings, "S3_URL_TTL", 604800)),
                                )
                            except Exception:
                                return None
        except Exception:
            return None
        return None

    def _load_documents(self, space: str) -> list[dict[str, Any]]:
        documents: list[dict[str, Any]] = []

        if space == "supreme_court":
            # Preferred path: S3 plain-text files (e.g. pdfs/text/txt/year/doc_id.txt)
            if (
                getattr(settings, "S3_BUCKET", None)
                and getattr(settings, "S3_TEXT_PREFIX", None)
                and boto3 is not None
            ):
                try:
                    client = self._get_s3_client()
                    bucket = settings.S3_BUCKET
                    prefix = str(settings.S3_TEXT_PREFIX).rstrip("/") + "/"
                    paginator = client.get_paginator("list_objects_v2")

                    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                        for obj in page.get("Contents", []):
                            key = obj.get("Key", "")
                            if not key.lower().endswith(".txt"):
                                continue
                            filename = key.rsplit("/", 1)[-1]
                            doc_id = filename.rsplit(".", 1)[0] or filename

                            try:
                                text_obj = client.get_object(Bucket=bucket, Key=key)
                                raw_bytes = text_obj["Body"].read()
                                try:
                                    text = raw_bytes.decode("utf-8")
                                except Exception:
                                    text = raw_bytes.decode("latin-1", errors="ignore")
                            except Exception:
                                continue

                            documents.append(
                                {
                                    "id": doc_id,
                                    "title": doc_id,
                                    "text": text,
                                    "space": space,
                                    "download_url": self._resolve_download_url(doc_id),
                                }
                            )
                except Exception as e:
                    print(f"[OpenSearch] Failed to load text documents from S3: {e}. Falling back to corpus.jsonl.")

            # Legacy path: S3 corpus.jsonl, if configured and no text docs were loaded
            if not documents and getattr(settings, "S3_BUCKET", None) and getattr(settings, "S3_CORPUS_KEY", None) and boto3 is not None:
                try:
                    client = self._get_s3_client()
                    obj = client.get_object(Bucket=settings.S3_BUCKET, Key=settings.S3_CORPUS_KEY)
                    body = obj["Body"]
                    # Iterate lines to avoid loading whole file into memory
                    for raw in body.iter_lines():
                        if not raw:
                            continue
                        try:
                            line = raw.decode("utf-8")
                            rec = json.loads(line)
                        except Exception:
                            continue
                        doc_id = rec.get("id") or rec.get("doc_id")
                        if not doc_id:
                            continue
                        title = rec.get("title", "")
                        text = rec.get("text", "")
                        documents.append({
                            "id": doc_id,
                            "title": title,
                            "text": text,
                            "space": space,
                            "download_url": self._resolve_download_url(doc_id),
                        })
                except Exception as e:
                    print(f"[OpenSearch] Failed to load corpus from S3: {e}. Falling back to filesystem.")

            # Filesystem fallback or if S3 not configured
            if not documents:
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
                        documents.append(
                            {
                                "id": doc_id,
                                "title": title,
                                "text": text,
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

    def _alias_name(self, space: str) -> str:
        # stable alias clients will search against
        safe = space.replace("/", "__").replace(" ", "_").lower()
        safe = re.sub(r"[^a-z0-9_\-]+", "-", safe)
        return f"{settings.OPENSEARCH_INDEX_PREFIX}-{safe}"

    def _build_index_name(self, space: str, suffix: str) -> str:
        # concrete index name for a build (timestamp)
        base = self._alias_name(space)
        return f"{base}-{suffix}"

    def _bulk_actions(self, index_name: str, docs: Iterable[dict[str, Any]]):
        for doc in docs:
            yield {
                "_op_type": "index",
                "_index": index_name,
                "_id": doc["id"],
                "_source": doc,
            }

    def _s3_doc_id(self, key: str) -> str:
        filename = key.rsplit("/", 1)[-1]
        stem = filename.rsplit(".", 1)[0] or filename
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip("-")
        return safe or str(abs(hash(key)))

    def _iter_s3_text_objects(self):
        if boto3 is None:
            raise RuntimeError("boto3 is required for S3 indexing but is not installed.")
        bucket = getattr(settings, "S3_BUCKET", None)
        prefix_raw = getattr(settings, "S3_TEXT_PREFIX", None)
        if not bucket or not prefix_raw:
            raise RuntimeError("S3_BUCKET and S3_TEXT_PREFIX are required for S3 incremental indexing.")

        client = self._get_s3_client()
        prefix = str(prefix_raw).rstrip("/") + "/"
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj.get("Key", "")
                if key.lower().endswith(".txt"):
                    yield obj

    def _existing_s3_etag(self, client: OpenSearch, index_name: str, doc_id: str) -> str | None:
        try:
            existing = client.get(index=index_name, id=doc_id, _source_includes=["s3_text_etag"])
        except NotFoundError:
            return None
        except Exception:
            return None
        source = existing.get("_source", {}) or {}
        return source.get("s3_text_etag")

    def _load_s3_text_doc(self, obj: dict[str, Any], space: str) -> dict[str, Any] | None:
        bucket = settings.S3_BUCKET
        key = obj.get("Key")
        if not bucket or not key:
            return None

        client = self._get_s3_client()
        try:
            text_obj = client.get_object(Bucket=bucket, Key=key)
            raw_bytes = text_obj["Body"].read()
            try:
                text = raw_bytes.decode("utf-8")
            except Exception:
                text = raw_bytes.decode("latin-1", errors="ignore")
        except Exception as e:
            print(f"[OpenSearch] Failed to read s3://{bucket}/{key}: {e}")
            return None

        doc_id = self._s3_doc_id(key)
        etag = str(obj.get("ETag", "")).strip('"')
        last_modified = obj.get("LastModified")
        last_modified_value = last_modified.isoformat() if hasattr(last_modified, "isoformat") else None

        return {
            "id": doc_id,
            "title": doc_id,
            "text": text,
            "space": space,
            "download_url": self._resolve_download_url(doc_id),
            "s3_text_key": key,
            "s3_text_etag": etag,
            "s3_last_modified": last_modified_value,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _wait_for_cluster(self, timeout=30):
        c = self._get_client()
        import time
        for _ in range(timeout):
            try:
                c.cluster.health(wait_for_status="yellow", request_timeout=5)
                return
            except Exception:
                time.sleep(1)
        raise RuntimeError("OpenSearch not ready")

    # ------------------------------------------------------------------
    # S3 helpers
    # ------------------------------------------------------------------
    def _get_s3_client(self):
        if self._s3_client is None:
            if boto3 is None:
                raise RuntimeError("boto3 is required for S3 operations but is not installed.")
            # Rely on environment/instance role for credentials
            self._s3_client = boto3.client("s3")
        return self._s3_client
    
    def _uses_sigv4(self) -> bool:
        return bool(getattr(settings, "OPENSEARCH_SIGV4", False))

    def _is_serverless(self):
        return self._uses_sigv4() and getattr(settings, "OPENSEARCH_AWS_SERVICE", "aoss") == "aoss"
    
    # ------------------------------------------------------------------
    # Public API (mirrors BM25Search)
    # ------------------------------------------------------------------
    def index(self, space: str = "supreme_court") -> None:
        print(f"[OpenSearch] Starting indexing for space '{space}'...")
        if not self._is_serverless():
            self._wait_for_cluster()
        
        print(f"[OpenSearch] Loading documents for space '{space}'...")
        client = self._get_client()
        alias = self._alias_name(space)

        documents = self._load_documents(space)
        if not documents:
            print(f"[OpenSearch] No documents to index for space '{space}'.")
            return
        
        print(f"[OpenSearch] Indexing {len(documents)} documents for space '{space}' into OpenSearch...")
        build_name = (
            alias if self._is_serverless() else self._build_index_name(space, suffix=str(int(__import__("time").time())))
        )

        # create build index (mapping/analyzer same as before)
        self._create_index_if_needed(client, build_name)

        # bulk index into build
        helpers.bulk(
            client,
            self._bulk_actions(build_name, documents),
            chunk_size=settings.OPENSEARCH_BULK_CHUNK_SIZE,
            refresh="wait_for",
            raise_on_error=False,
            raise_on_exception=False,
        )

        if not self._is_serverless():
            # alias swap (atomic)
            actions = []
            if client.indices.exists_alias(name=alias):
                olds = list(client.indices.get_alias(name=alias).keys())
                for o in olds:
                    actions.append({"remove": {"index": o, "alias": alias}})
            actions.append({"add": {"index": build_name, "alias": alias}})
            client.indices.update_aliases(body={"actions": actions})

            # optional: clean up old indices with same prefix (keep last N)
            keep_n = 2
            all_idxs = [i for i in client.indices.get_alias(index=f"{alias}-*").keys()]
            # sort by name (timestamp suffix makes this work)
            for old in sorted(all_idxs)[:-keep_n]:
                if old != build_name:
                    client.indices.delete(index=old, ignore=[404])

            print(f"[OpenSearch] Indexed {len(documents)} docs into alias '{alias}' via '{build_name}'.")
        else:
            print(f"[OpenSearch] Indexed {len(documents)} docs into serverless index '{build_name}'.")

    def index_incremental(
        self,
        space: str = "supreme_court",
        delete_missing: bool | None = None,
        progress_every: int = 500,
    ) -> dict[str, int]:
        """Incrementally index S3 text files into the stable space index.

        Intended for one-off ECS jobs, not FastAPI startup. Stores S3 key/ETag
        metadata and skips documents whose ETag is unchanged.
        """
        if space != "supreme_court":
            raise RuntimeError("Incremental S3 indexing is currently only supported for supreme_court.")
        if not getattr(settings, "S3_BUCKET", None) or not getattr(settings, "S3_TEXT_PREFIX", None):
            raise RuntimeError("S3_BUCKET and S3_TEXT_PREFIX must be configured for incremental indexing.")

        progress_every = max(1, progress_every)
        started_at = time.monotonic()

        print(f"[OpenSearch] Starting incremental indexing for space '{space}'.", flush=True)
        if not self._is_serverless():
            self._wait_for_cluster()

        client = self._get_client()
        index_name = self._alias_name(space)
        self._create_index_if_needed(client, index_name)

        delete_missing = (
            getattr(settings, "OPENSEARCH_DELETE_MISSING_S3_DOCS", False)
            if delete_missing is None
            else delete_missing
        )

        seen_ids: set[str] = set()
        stats = {
            "seen": 0,
            "skipped": 0,
            "indexed": 0,
            "failed": 0,
            "deleted": 0,
            "bytes_seen": 0,
            "bytes_indexed": 0,
        }

        def log_progress(label: str) -> None:
            elapsed = max(time.monotonic() - started_at, 0.001)
            files_per_min = stats["seen"] / (elapsed / 60)
            mb_seen = stats["bytes_seen"] / (1024 * 1024)
            mb_indexed = stats["bytes_indexed"] / (1024 * 1024)
            print(
                "[OpenSearch] "
                f"{label}: seen={stats['seen']} indexed={stats['indexed']} "
                f"skipped={stats['skipped']} failed={stats['failed']} deleted={stats['deleted']} "
                f"scanned={mb_seen:.1f}MiB changed={mb_indexed:.1f}MiB "
                f"elapsed={elapsed:.0f}s rate={files_per_min:.1f} files/min.",
                flush=True,
            )

        print(
            "[OpenSearch] Incremental source: "
            f"s3://{settings.S3_BUCKET}/{str(settings.S3_TEXT_PREFIX).rstrip('/')}/ -> "
            f"index '{index_name}', progress_every={progress_every}, delete_missing={delete_missing}.",
            flush=True,
        )

        def actions():
            for obj in self._iter_s3_text_objects():
                stats["seen"] += 1
                size = int(obj.get("Size") or 0)
                stats["bytes_seen"] += size

                key = obj.get("Key", "")
                doc_id = self._s3_doc_id(key)
                seen_ids.add(doc_id)
                etag = str(obj.get("ETag", "")).strip('"')

                if etag and self._existing_s3_etag(client, index_name, doc_id) == etag:
                    stats["skipped"] += 1
                    if stats["seen"] % progress_every == 0:
                        log_progress("progress")
                    continue

                doc = self._load_s3_text_doc(obj, space)
                if not doc:
                    stats["failed"] += 1
                    if stats["seen"] % progress_every == 0:
                        log_progress("progress")
                    continue

                stats["indexed"] += 1
                stats["bytes_indexed"] += size
                if stats["seen"] % progress_every == 0:
                    log_progress("progress")

                yield {
                    "_op_type": "index",
                    "_index": index_name,
                    "_id": doc["id"],
                    "_source": doc,
                }

        helpers.bulk(
            client,
            actions(),
            chunk_size=settings.OPENSEARCH_BULK_CHUNK_SIZE,
            refresh="wait_for",
            raise_on_error=False,
            raise_on_exception=False,
        )
        log_progress("bulk indexing finished")

        if delete_missing:
            print("[OpenSearch] Checking for indexed S3 documents missing from current S3 listing.", flush=True)
            response = client.search(
                index=index_name,
                body={
                    "size": 10000,
                    "_source": False,
                    "query": {"exists": {"field": "s3_text_key"}},
                },
                scroll="2m",
            )
            scroll_id = response.get("_scroll_id")
            while True:
                hits = response.get("hits", {}).get("hits", [])
                if not hits:
                    break
                delete_actions = [
                    {"_op_type": "delete", "_index": index_name, "_id": hit["_id"]}
                    for hit in hits
                    if hit.get("_id") not in seen_ids
                ]
                if delete_actions:
                    for ok, _ in helpers.streaming_bulk(client, delete_actions, raise_on_error=False):
                        if ok:
                            stats["deleted"] += 1
                            if stats["deleted"] % progress_every == 0:
                                log_progress("delete progress")
                if not scroll_id:
                    break
                response = client.scroll(scroll_id=scroll_id, scroll="2m")
                scroll_id = response.get("_scroll_id")
            if scroll_id:
                client.clear_scroll(scroll_id=scroll_id, ignore=[404])

        log_progress("incremental indexing complete")
        return stats

    def has_space(self, space: str) -> bool:
        """Return True if the logical space exists (alias or index)."""
        client = self._get_client()
        alias = self._alias_name(space)
        if client.indices.exists_alias(name=alias):
            return True
        try:
            return bool(client.indices.exists(index=alias))
        except Exception:
            return False

    def search(self, query: str, top_k: int = 30, space: str = "supreme_court") -> list[dict[str, Any]]:
        client = self._get_client()
        alias = self._alias_name(space)
        target_index = alias
        if not client.indices.exists_alias(name=alias):
            if not client.indices.exists(index=alias):
                print(f"[OpenSearch] Alias/index '{alias}' missing for space '{space}'.")
                return []

        body = {
            "size": top_k,
            "timeout": f"{settings.OPENSEARCH_SEARCH_TIMEOUT}s",
            "track_total_hits": False,
            "_source": {"includes": ["id", "title", "download_url"]},
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "text"],
                    "type": "best_fields",
                }
            },
        }

        if settings.OPENSEARCH_ENABLE_HIGHLIGHTS:
            body["highlight"] = {
                "fields": {
                    "text": {
                        "fragment_size": settings.OPENSEARCH_HIGHLIGHT_FRAGMENT_SIZE,
                        "number_of_fragments": 1,
                    }
                }
            }

        response = client.search(
            index=target_index,
            body=body,
            request_timeout=settings.OPENSEARCH_SEARCH_TIMEOUT,
        )
        hits: list[dict[str, Any]] = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            snippet = ""
            highlight = hit.get("highlight", {}).get("text")
            if highlight:
                snippet = " ... ".join(highlight)
            else:
                snippet = source.get("title", "")
            dl_url = source.get("download_url")
            if not dl_url and getattr(settings, "S3_PRESIGN_ON_SEARCH", False):
                dl_url = self._presign_by_id(source.get("id") or hit.get("_id"))
            hits.append(
                {
                    "id": source.get("id") or hit.get("_id"),
                    "title": source.get("title", ""),
                    "score": float(hit.get("_score") or 0.0),
                    "snippet": snippet,
                    "download_url": dl_url,
                }
            )
        return hits

    def get_document_by_id(self, space: str, doc_id: str) -> dict[str, Any] | None:
        client = self._get_client()
        alias = self._alias_name(space)
        try:
            doc = client.get(index=alias, id=doc_id)
        except NotFoundError:
            return None

        source = doc.get("_source", {})
        dl_url = source.get("download_url")
        if not dl_url and getattr(settings, "S3_PRESIGN_ON_QUERY", True):
            dl_url = self._presign_by_id(doc_id)
        return {
            "id": doc_id,
            "title": source.get("title", ""),
            "text": source.get("text", ""),
            "download_url": dl_url,
        }

    def fetch_passages(
        self,
        *,
        space: str,
        doc_id: str,
        query: str,
        per_id: int = 3,
        max_tokens: int = 350,
        chars_per_token: int = 4,
    ) -> list[dict]:
        """
        Return up to `per_id` passages from the given doc that best match `query`.
        Each passage is approximately `max_tokens` tokens.
        """
        client = self._get_client()
        alias = self._alias_name(space)
        target_index = alias
        if not client.indices.exists_alias(name=alias):
            if not client.indices.exists(index=alias):
                return []

        fragment_size = max(128, min(8192, int(max_tokens * chars_per_token)))

        body = {
            "size": 1,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"id": doc_id}},
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "text"],
                                "type": "best_fields",
                            }
                        },
                    ]
                }
            },
            "highlight": {
                "order": "score",
                "fields": {
                    "text": {
                        "type": "unified",
                        "fragment_size": fragment_size,
                        "number_of_fragments": per_id,
                        "no_match_size": fragment_size,
                        "pre_tags": ["<em>"],
                        "post_tags": ["</em>"],
                    }
                },
            },
            "_source": {"includes": ["id", "title", "download_url"]},
        }

        res = client.search(index=target_index, body=body)
        hits = res.get("hits", {}).get("hits", [])
        if not hits:
            return []

        hit = hits[0]
        frags = hit.get("highlight", {}).get("text", []) or []

        passages = []
        for i, frag in enumerate(frags[:per_id]):
            dl_url = hit.get("_source", {}).get("download_url")
            if not dl_url and getattr(settings, "S3_PRESIGN_ON_QUERY", True):
                dl_url = self._presign_by_id(doc_id)
            passages.append(
                {
                    "doc_id": doc_id,
                    "rank": i + 1,
                    "passage": frag,
                    "approx_tokens": fragment_size // chars_per_token,
                    "score": float(hit.get("_score") or 0.0),
                    "title": hit.get("_source", {}).get("title", ""),
                    "download_url": dl_url,
                }
            )

        if not passages:
            print("[OpenSearch] Highlighter returned no passages; only returning snippet of document.")
            doc = self.get_document_by_id(space, doc_id)
            if not doc:
                return []
            text = doc.get("text", "") or ""
            snippet = text[:fragment_size]
            passages = [
                {
                    "doc_id": doc_id,
                    "rank": 1,
                    "passage": snippet,
                    "approx_tokens": fragment_size // chars_per_token,
                    "score": 0.0,
                    "title": doc.get("title", ""),
                    "download_url": doc.get("download_url"),
                }
            ]

        return passages


opensearch_engine = OpenSearchSearch()
