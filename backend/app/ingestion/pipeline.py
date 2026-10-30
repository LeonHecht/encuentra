from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import replace
from datetime import datetime, timezone
from itertools import islice
from uuid import uuid4

from .extraction import EXTRACTOR_VERSION, extract_pdf
from .models import DocumentRef, Source
from .storage import Store, json_bytes

logger = logging.getLogger(__name__)
SCHEMA_VERSION = 1


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Collector:
    """One writer per source/prefix. State and immutable revisions survive restarts."""

    def __init__(self, source: Source, client, store: Store, *, min_page_characters=20):
        if not re.fullmatch(r"[a-z0-9_-]+", source.name):
            raise ValueError("Invalid source name")
        self.source, self.client, self.store = source, client, store
        self.extraction_policy = {
            "version": EXTRACTOR_VERSION,
            "min_page_characters": min_page_characters,
        }

    def _json(self, key, value):
        self.store.put(key, json_bytes(value), "application/json; charset=utf-8")

    def _archive(self, key, data, content_type):
        if not self.store.exists(key):
            self.store.put(key, data, content_type)

    def _complete(self, state):
        return (
            state
            and state.get("schema_version") == SCHEMA_VERSION
            and state.get("extraction_policy") == self.extraction_policy
            and state.get("status") in ("ready", "needs_ocr")
            and state.get("required_keys")
            and all(self.store.exists(key) for key in state["required_keys"])
        )

    def collect(self, ref: DocumentRef, *, refresh=False) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", ref.source_id):
            raise ValueError("Invalid source document ID")
        doc_id = f"{self.source.name}-{ref.source_id}"
        state_key = f"{self.source.name}/state/{doc_id}.json"
        previous = self.store.read_json(state_key)
        if not refresh and self._complete(previous):
            return {"id": doc_id, "result": "skipped", "status": previous["status"]}

        # A direct ID refresh can reuse previously discovered catalog metadata.
        # A new catalog discovery always takes precedence over this fallback.
        if not ref.catalog_data and previous and previous.get("catalog_data"):
            ref = replace(
                ref,
                catalog_data=previous["catalog_data"],
                catalog_year=previous.get("catalog_year", ref.catalog_year),
            )

        checked_at = now()
        pending = {
            "id": doc_id,
            "source": self.source.name,
            "source_id": ref.source_id,
            "source_url": ref.url,
            "status": "pending",
            "last_checked_at": checked_at,
            "storage_year": (previous or {}).get("storage_year"),
        }
        if ref.catalog_data:
            pending.update(catalog_data=ref.catalog_data, catalog_year=ref.catalog_year)
        # A crash during publication must trigger repair on the next run.
        self._json(state_key, pending)
        try:
            fetched = self.source.fetch(self.client, ref)
            if fetched.detail_format not in ("html", "json"):
                raise ValueError("Unsupported source snapshot format")
            detail_content_type = (
                "application/json" if fetched.detail_format == "json" else "text/html"
            ) + "; charset=utf-8"
            raw_hash, detail_hash = sha256(fetched.original), sha256(fetched.detail_html)
            revision = sha256(
                json_bytes(
                    {
                        "original_sha256": raw_hash,
                        "detail_sha256": detail_hash,
                        "metadata": fetched.metadata,
                        "schema_version": SCHEMA_VERSION,
                        "extraction_policy": self.extraction_policy,
                    }
                )
            )
            if previous and previous.get("revision") == revision and self._complete(previous):
                previous["last_checked_at"] = checked_at
                self._json(state_key, previous)
                return {"id": doc_id, "result": "unchanged", "status": previous["status"]}

            # Fix the export year at first publication so corrected dates do not
            # create a second canonical document during subsequent refreshes.
            year = (previous or {}).get("storage_year")
            if not year:
                date = fetched.metadata.get("issued_at") or fetched.metadata.get("published_at")
                year = str(date[:4] if date else fetched.ref.catalog_year or "undated")
            pending["storage_year"] = year
            archive = f"{self.source.name}/versions/{doc_id}/{revision}"
            keys = {
                "original": f"{self.source.name}/files/{year}/{doc_id}.PDF",
                "text": f"{self.source.name}/text/{year}/{doc_id}.txt",
                "pages": f"{self.source.name}/pages/{year}/{doc_id}.json",
                "metadata": f"{self.source.name}/metadata/{year}/{doc_id}.json",
            }
            version_keys = {
                "original": f"{archive}/original.PDF",
                "detail": f"{archive}/detail.{fetched.detail_format}",
                "text": f"{archive}/text.txt",
                "pages": f"{archive}/pages.json",
                "metadata": f"{archive}/metadata.json",
            }
            # Retain originals even when extraction fails.
            self._archive(version_keys["original"], fetched.original, "application/pdf")
            self._archive(version_keys["detail"], fetched.detail_html, detail_content_type)
            pending["archived_original_key"] = self.store.object_key(version_keys["original"])
            extraction = extract_pdf(
                fetched.original, self.extraction_policy["min_page_characters"]
            )
            text = extraction.pop("text").encode("utf-8")
            pages = json_bytes(extraction)
            status = extraction["status"]
            canonical_keys = dict(keys)
            if status != "ready":
                canonical_keys.pop("text")
            manifest = {
                **fetched.metadata,
                "schema_version": SCHEMA_VERSION,
                "id": doc_id,
                "source": self.source.name,
                "source_id": ref.source_id,
                "source_url": ref.url,
                "original_url": fetched.original_url,
                "country": "SV",
                "language": "es",
                "revision": revision,
                "status": status,
                "indexable": status == "ready",
                "storage_year": year,
                "fetched_at": checked_at,
                "original_sha256": raw_hash,
                "detail_sha256": detail_hash,
                "text_sha256": sha256(text),
                "response_headers": fetched.response_headers,
                "extraction_policy": self.extraction_policy,
                "page_count": extraction["page_count"],
                "ocr_candidate_pages": extraction["ocr_candidate_pages"],
                "bucket": getattr(self.store, "bucket", None),
                "artifacts": {k: self.store.object_key(v) for k, v in canonical_keys.items()},
                "version_artifacts": {k: self.store.object_key(v) for k, v in version_keys.items()},
            }
            if ref.catalog_data:
                manifest.update(catalog_data=ref.catalog_data, catalog_year=ref.catalog_year)
            archived_manifest = self.store.read_json(version_keys["metadata"])
            if archived_manifest is not None:
                manifest = archived_manifest
            self._archive(version_keys["text"], text, "text/plain; charset=utf-8")
            self._archive(version_keys["pages"], pages, "application/json; charset=utf-8")
            self._archive(
                version_keys["metadata"], json_bytes(manifest), "application/json; charset=utf-8"
            )
            self.store.put(keys["original"], fetched.original, "application/pdf")
            self.store.put(keys["pages"], pages, "application/json; charset=utf-8")
            if status == "ready":
                self.store.put(keys["text"], text, "text/plain; charset=utf-8")
            else:
                # Keep partial extraction in the revision, outside the indexable prefix.
                self.store.delete(keys["text"])
            self._json(keys["metadata"], manifest)
            self._json(
                state_key,
                {
                    **manifest,
                    "last_checked_at": checked_at,
                    "required_keys": list(canonical_keys.values()) + list(version_keys.values()),
                },
            )
            return {
                "id": doc_id,
                "result": "stored",
                "status": status,
                "metadata_key": self.store.object_key(keys["metadata"]),
            }
        except Exception as exc:
            self._json(state_key, {**pending, "status": "failed", "error": str(exc)})
            raise

    def run(self, refs, *, refresh=False, limit=None) -> dict:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        report = {
            "run_id": run_id,
            "source": self.source.name,
            "started_at": now(),
            "stored": 0,
            "skipped": 0,
            "unchanged": 0,
            "failed": 0,
            "needs_ocr": 0,
            "records": [],
            "status": "running",
        }
        report_key = f"{self.source.name}/runs/{run_id}.json"
        self._json(report_key, report)
        try:
            for ref in islice(refs, limit):
                try:
                    record = self.collect(ref, refresh=refresh)
                    report[record["result"]] += 1
                    report["needs_ocr"] += int(record["status"] == "needs_ocr")
                    logger.info("%s %s (%s)", record["result"], record["id"], record["status"])
                except Exception as exc:
                    logger.exception("Failed to collect %s", ref.url)
                    report["failed"] += 1
                    record = {
                        "source_id": ref.source_id,
                        "source_url": ref.url,
                        "result": "failed",
                        "error": str(exc),
                    }
                report["records"].append(record)
            report["status"] = "failed" if report["failed"] else "complete"
        except KeyboardInterrupt:
            report["status"] = "interrupted"
        except Exception as exc:
            logger.exception("Discovery/run failed")
            report.update(status="failed", discovery_error=str(exc))
        finally:
            report["finished_at"] = now()
            self._json(report_key, report)
        report["report_key"] = self.store.object_key(report_key)
        return report
