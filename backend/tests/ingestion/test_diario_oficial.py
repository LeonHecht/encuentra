from __future__ import annotations

import json

import pytest

from backend.app.ingestion.diario_oficial import (
    BASE,
    DOCUMENTS_URL,
    MONTHS_URL,
    DiarioOficialSource,
)
from backend.app.ingestion.http import Response
from backend.app.ingestion.pipeline import Collector
from backend.app.ingestion.storage import LocalStore, json_bytes
from backend.app.jobs import scrape_legislation
from backend.tests.ingestion.test_collector import pdf_bytes

# Observed API fields, including an approximate historical archive date.
CURRENT = {
    "Id": "31859",
    "FechaInicio": "2026-10-01",
    "FechaInexacta": "0",
    "NombreArchivo": "01-10-2026.pdf",
}
HISTORICAL = {
    "Id": "11",
    "FechaInicio": "1847-01-01",
    "FechaInexacta": "1",
    "NombreArchivo": "1847_Parte19.pdf",
}
HOME = b'<select id="year"><option value="2026">2026</option><option value="1847">1847</option></select>'


class Client:
    def __init__(self, *, rows=None, headers=None):
        self.rows = rows if rows is not None else [CURRENT]
        self.headers = (
            headers
            if headers is not None
            else {
                "content-disposition": "attachment;filename=01-10-2026.pdf",
                "content-type": "application/pdf",
            }
        )
        self.home = HOME
        self.months = [{"month": "10"}]
        self.original = pdf_bytes()
        self.calls = []

    def get(self, url):
        self.calls.append(("GET", url, None))
        return Response(url, self.home if url == BASE + "/" else self.original, self.headers, 200)

    def post(self, url, *, data):
        self.calls.append(("POST", url, data))
        body = self.months if url == MONTHS_URL else {"data": self.rows}
        return Response(url, json_bytes(body), {"content-type": "application/json"}, 200)

    def close(self):
        pass


def test_discovery_uses_public_form_endpoints_and_carries_catalog_metadata():
    client = Client(rows=[CURRENT, CURRENT])
    client.months = [{"month": "9"}, {"month": "10"}]
    refs = list(DiarioOficialSource().discover(client, [2026], months=[10]))
    assert len(refs) == 1
    assert refs[0].source_id == "31859"
    assert refs[0].url == BASE + "/seleccion/31859"
    assert refs[0].catalog_year == 2026
    assert refs[0].catalog_data["record"] == CURRENT
    assert client.calls == [
        ("GET", BASE + "/", None),
        ("POST", MONTHS_URL, {"year": 2026}),
        ("POST", DOCUMENTS_URL, {"year": 2026, "month": 10}),
    ]


def test_all_years_and_duplicate_records_across_months():
    client = Client()
    client.months = [1, {"mes": "2"}, "2"]
    refs = list(DiarioOficialSource().discover(client, None))
    assert len(refs) == 1  # Stable archive ID, even when catalogs repeat it.
    queries = [call[2] for call in client.calls if call[1] == DOCUMENTS_URL]
    assert queries == [
        {"year": 2026, "month": 2},
        {"year": 2026, "month": 1},
        {"year": 1847, "month": 2},
        {"year": 1847, "month": 1},
    ]


def test_advertised_month_with_no_records_is_valid_empty_result():
    assert list(DiarioOficialSource().discover(Client(rows=[]), [2026])) == []


def test_unadvertised_month_is_not_requested():
    client = Client()
    assert list(DiarioOficialSource().discover(client, [2026], months=[12])) == []
    assert all(url != DOCUMENTS_URL for _, url, _ in client.calls)


def test_unknown_year_and_changed_homepage_fail_visibly():
    client = Client()
    with pytest.raises(ValueError, match="Years absent"):
        list(DiarioOficialSource().discover(client, [1900]))
    assert len(client.calls) == 1
    client.home = b"<html>Challenge page</html>"
    with pytest.raises(ValueError, match="no years"):
        list(DiarioOficialSource().discover(client, None))


@pytest.mark.parametrize("months", [{"error": "blocked"}, [{"changed_field": "10"}], [13], [True]])
def test_unexpected_month_payload_is_not_a_successful_empty_crawl(months):
    client = Client()
    client.months = months
    with pytest.raises(ValueError):
        list(DiarioOficialSource().discover(client, [2026]))


@pytest.mark.parametrize(
    "body", [b"<html>Challenge</html>", b'{"error":"blocked"}', b'{"data":{}}', b"[]"]
)
def test_unexpected_document_response_fails(body):
    class BrokenClient(Client):
        def post(self, url, *, data):
            if url == DOCUMENTS_URL:
                return Response(url, body, {}, 200)
            return super().post(url, data=data)

    with pytest.raises(ValueError):
        list(DiarioOficialSource().discover(BrokenClient(), [2026]))


@pytest.mark.parametrize(
    "row",
    [
        {"Id": "bad", "NombreArchivo": "x.pdf"},
        {"Id": "1"},
        {"Id": "1", "NombreArchivo": ""},
        "unexpected",
    ],
)
def test_malformed_catalog_record_fails(row):
    with pytest.raises(ValueError):
        list(DiarioOficialSource().discover(Client(rows=[row]), [2026]))


def test_current_edition_has_exact_catalog_date_and_json_snapshot():
    source, client = DiarioOficialSource(), Client()
    ref = next(source.discover(client, [2026]))
    fetched = source.fetch(client, ref)
    assert fetched.metadata["document_type"] == "official_gazette"
    assert fetched.metadata["document_granularity"] == "archive_file"
    assert fetched.metadata["published_at"] == "2026-10-01"
    assert fetched.metadata["publication_date_precision"] == "day"
    assert fetched.metadata["official_gazette_number"] is None
    assert fetched.metadata["legal_status"] == "unverified"
    assert fetched.detail_format == "json"
    snapshot = json.loads(fetched.detail_html)
    assert snapshot["record"] == CURRENT
    assert snapshot["query"] == {"year": 2026, "month": 10}
    assert len([c for c in client.calls if c[0] == "GET" and "/seleccion/" in c[1]]) == 1


@pytest.mark.parametrize(
    "changes",
    [{"FechaInicio": "not a date"}, {"FechaInexacta": None}, {"FechaInexacta": "unexpected"}],
)
def test_missing_or_invalid_catalog_precision_does_not_invent_an_exact_date(changes):
    row = {**CURRENT, **changes}
    source, client = DiarioOficialSource(), Client(rows=[row])
    fetched = source.fetch(client, next(source.discover(client, [2026])))
    assert fetched.metadata["published_at"] is None
    assert fetched.metadata["publication_date_precision"] == "unknown"
    assert fetched.metadata["source_fields"] == row


def test_historical_part_does_not_claim_an_exact_publication_date(tmp_path):
    source, client = DiarioOficialSource(), Client(rows=[HISTORICAL], headers={})
    client.months = [{"month": "1"}]
    ref = next(source.discover(client, [1847]))
    fetched = source.fetch(client, ref)
    assert fetched.metadata["publication_date_precision"] == "approximate"
    assert fetched.metadata["published_at"] is None
    assert fetched.metadata["catalog_date"] == "1847-01-01"
    assert fetched.metadata["source_filename"] == "1847_Parte19.pdf"
    collector = Collector(source, client, LocalStore(tmp_path))
    collector.collect(ref)
    assert (tmp_path / "diario_oficial/files/1847/diario_oficial-11.PDF").exists()


def test_direct_download_uses_filename_for_storage_year_without_asserting_exact_date(tmp_path):
    source, client = DiarioOficialSource(), Client()
    ref = source.reference("31859")
    fetched = source.fetch(client, ref)
    assert fetched.ref.catalog_year == 2026
    assert fetched.metadata["filename_date"] == "2026-10-01"
    assert fetched.metadata["published_at"] is None
    assert fetched.metadata["publication_date_precision"] == "unknown"
    Collector(source, client, LocalStore(tmp_path)).collect(ref)
    assert (tmp_path / "diario_oficial/files/2026/diario_oficial-31859.PDF").exists()
    assert all(method == "GET" and "/seleccion/" in url for method, url, _ in client.calls)


@pytest.mark.parametrize("source_id", ["../file", "1/2", "0", "-1", "1.5", "１２", ""])
def test_invalid_archive_id_is_rejected(source_id):
    with pytest.raises(ValueError):
        DiarioOficialSource.reference(source_id)


def test_catalog_collection_json_archive_resume_and_direct_refresh(tmp_path):
    class RecordingStore(LocalStore):
        def __init__(self, path):
            super().__init__(path)
            self.types = {}

        def put(self, key, data, content_type):
            self.types[key] = content_type
            super().put(key, data, content_type)

    source, client = DiarioOficialSource(), Client()
    ref = next(source.discover(client, [2026]))
    store = RecordingStore(tmp_path)
    collector = Collector(source, client, store)
    collector.collect(ref)
    first = store.read_json("diario_oficial/state/diario_oficial-31859.json")
    detail_key = first["version_artifacts"]["detail"]
    assert detail_key.endswith("/detail.json")
    assert store.types[detail_key] == "application/json; charset=utf-8"
    assert first["published_at"] == "2026-10-01"
    assert collector.collect(ref)["result"] == "skipped"
    # No catalog metadata is lost when refreshing via --document-ids later.
    assert collector.collect(source.reference("31859"), refresh=True)["result"] == "unchanged"
    second = store.read_json("diario_oficial/state/diario_oficial-31859.json")
    assert second["revision"] == first["revision"]
    assert second["published_at"] == first["published_at"]


def test_catalog_metadata_update_retains_previous_revision(tmp_path):
    source, client = DiarioOficialSource(), Client()
    store = LocalStore(tmp_path)
    collector = Collector(source, client, store)
    collector.collect(next(source.discover(client, [2026])))
    first = store.read_json("diario_oficial/state/diario_oficial-31859.json")
    client.rows = [{**CURRENT, "FechaInexacta": "1"}]
    collector.collect(next(source.discover(client, [2026])), refresh=True)
    second = store.read_json("diario_oficial/state/diario_oficial-31859.json")
    assert second["revision"] != first["revision"]
    assert first["original_sha256"] == second["original_sha256"]
    assert second["published_at"] is None
    assert store.exists(first["version_artifacts"]["original"])


def test_cli_diario_catalog_and_month_filter(tmp_path, monkeypatch):
    client = Client()
    monkeypatch.setattr(scrape_legislation, "HttpClient", lambda *args, **kwargs: client)
    assert (
        scrape_legislation.main(
            [
                "--source",
                "diario_oficial",
                "--years",
                "2026",
                "--months",
                "10",
                "--limit",
                "1",
                "--output",
                str(tmp_path),
            ]
        )
        == 0
    )
    root = tmp_path / "legislation/diario_oficial"
    assert (root / "text/2026/diario_oficial-31859.txt").exists()
    assert (root / "pages/2026/diario_oficial-31859.json").exists()
    assert (root / "metadata/2026/diario_oficial-31859.json").exists()


@pytest.mark.parametrize(
    "args",
    [
        ["--years", "2026", "--months", "10"],
        ["--source", "diario_oficial", "--years", "2026", "--months", "13"],
        ["--source", "diario_oficial", "--document-ids", "31859", "--months", "10"],
    ],
)
def test_cli_rejects_invalid_month_scope(args, tmp_path):
    with pytest.raises(SystemExit) as error:
        scrape_legislation.main([*args, "--output", str(tmp_path)])
    assert error.value.code == 2
