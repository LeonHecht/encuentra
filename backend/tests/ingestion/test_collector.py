from __future__ import annotations

from io import BytesIO
from pathlib import Path

import boto3
import pytest
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
from botocore.stub import Stubber
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from backend.app.ingestion.asamblea import BASE, INDEX_PATH, AsambleaSource
from backend.app.ingestion.extraction import extract_pdf
from backend.app.ingestion.http import Response
from backend.app.ingestion.models import FetchedDocument
from backend.app.ingestion.pipeline import Collector
from backend.app.ingestion.storage import LocalStore, S3Store, checked_key, json_bytes

FIXTURES = Path(__file__).parent / "fixtures"
PDF_URL = BASE + "/sites/default/files/documents/decretos/4B2D90B7-98D4-467D-8126-2E180D938095.pdf"


def pdf_bytes(
    text="Articulo 1. Texto legal para comprobar la extraccion.", blank=False, password=None
):
    writer = PdfWriter()
    page = writer.add_blank_page(612, 792)
    if not blank:
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
        )
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    if password is not None:
        writer.encrypt(password, algorithm="AES-256")
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


class FixtureClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url):
        self.calls.append(url)
        return Response(url, self.responses[url], {"content-type": "application/pdf"}, 200)

    def validate_url(self, url):
        assert url.startswith(BASE + "/")

    def close(self):
        pass


def test_detail_parses_publication_columns_and_keeps_native_id():
    source = AsambleaSource()
    ref = source.reference("4530")
    client = FixtureClient({ref.url: (FIXTURES / "detail.html").read_bytes(), PDF_URL: pdf_bytes()})
    fetched = source.fetch(client, ref)
    assert fetched.metadata["title"] == "LEY BITCOIN."
    assert fetched.metadata["decree_number"] == "57"
    assert fetched.ref.source_id == "4530"  # Decree numbers are not globally unique.
    assert fetched.metadata["issued_at"] == "2021-06-08"
    assert fetched.metadata["published_at"] == "2021-06-09"
    assert fetched.metadata["official_gazette_number"] == "110"
    assert fetched.metadata["official_gazette_volume"] == "431"
    assert fetched.metadata["document_type"] == "law"
    assert fetched.metadata["legal_status"] == "unverified"
    assert fetched.metadata["subject"] == "Instituciones Financieras"


def test_reform_is_preserved_as_separate_decree():
    source = AsambleaSource()
    html = (FIXTURES / "reform.html").read_bytes()
    from bs4 import BeautifulSoup

    url = BeautifulSoup(html, "html.parser").select_one('a[href*=".pdf"]')["href"]
    fetched = source.fetch(
        FixtureClient({source.reference("6108").url: html, url: pdf_bytes()}),
        source.reference("6108"),
    )
    assert fetched.metadata["document_type"] == "decree"
    assert fetched.metadata["decree_number"] == "199"
    assert fetched.metadata["published_at"] == "2025-01-30"


def test_catalog_record_without_pdf_is_reported_and_retryable(tmp_path):
    from bs4 import BeautifulSoup

    html = BeautifulSoup((FIXTURES / "detail.html").read_bytes(), "html.parser")
    for link in html.select("a"):
        link.decompose()
    source = AsambleaSource()
    ref = source.reference("4530")
    client = FixtureClient({ref.url: str(html).encode()})
    collector = Collector(source, client, LocalStore(tmp_path))
    for _ in range(2):
        report = collector.run([ref])
        assert report["failed"] == 1 and report["status"] == "failed"
        assert "Expected one PDF link, found 0" in report["records"][0]["error"]
    assert len(client.calls) == 2


def test_discovery_deduplicates_modals_and_follows_pagination():
    root = BASE + INDEX_PATH
    year = root + "/2021/0"
    second = year + "?page=1"
    card = '<a data-al-modal-url="/leyes-y-decretos/view/4530 #asamblea-contenido">57</a>'
    responses = {
        root: b'<div id="asamblea-contenido"><a href="/leyes-y-decretos/decretos-por-anios/2021/0">2021</a></div>',
        year: f'<div id="asamblea-contenido">{card}{card}<div class="pager"><a href="?page=1">Next</a></div></div>'.encode(),
        second: f'<div id="asamblea-contenido">{card}<a href="/leyes-y-decretos/view/6108">199</a><a rel="next" href="{year}">Back</a></div>'.encode(),
    }
    client = FixtureClient(responses)
    refs = list(AsambleaSource().discover(client, None))
    assert [r.source_id for r in refs] == ["4530", "6108"]
    assert all(r.catalog_year == 2021 for r in refs)
    assert client.calls == [root, year, second]


@pytest.mark.parametrize(
    "html",
    [b"<html>Cloudflare challenge</html>", b'<div id="asamblea-contenido">Changed layout</div>'],
)
def test_missing_catalog_layout_is_not_successful_empty_crawl(html):
    url = BASE + INDEX_PATH + "/2021/0"
    with pytest.raises(ValueError):
        list(AsambleaSource().discover(FixtureClient({url: html}), [2021]))


def test_pdf_prefix_and_page_offsets():
    original = b"12345678" + pdf_bytes()
    result = extract_pdf(original)
    assert result["status"] == "ready"
    assert result["pdf_header_offset"] == 8
    page = result["pages"][0]
    assert result["text"][page["start"] : page["end"]] == page["text"]
    assert "Articulo 1." in page["text"]


def test_multiple_page_boundaries_roundtrip():
    one_page = pdf_bytes()
    from pypdf import PdfReader

    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(one_page)))
    writer.append(PdfReader(BytesIO(one_page)))
    data = BytesIO()
    writer.write(data)
    result = extract_pdf(data.getvalue())
    assert result["page_count"] == 2
    first, second = result["pages"]
    assert second["start"] == first["end"] + 2
    for page in result["pages"]:
        assert result["text"][page["start"] : page["end"]] == page["text"]


@pytest.mark.parametrize("data", [b"<html>Not a PDF</html>", b"%PDF-broken"])
def test_invalid_downloads_are_rejected(data):
    with pytest.raises(Exception):
        extract_pdf(data)


def test_scanned_candidate_and_standard_empty_password_pdf():
    assert extract_pdf(pdf_bytes(blank=True))["ocr_candidate_pages"] == [1]
    assert extract_pdf(pdf_bytes(password=""))["status"] == "ready"
    with pytest.raises(ValueError, match="opening password"):
        extract_pdf(pdf_bytes(password="private"))


class SampleSource:
    name = "asamblea"
    allowed_hosts = {"www.asamblea.gob.sv"}

    def __init__(self):
        self.calls = 0
        self.original = pdf_bytes()
        self.title = "LEY DE PRUEBA"

    def fetch(self, client, ref):
        self.calls += 1
        return FetchedDocument(
            ref,
            {"title": self.title, "issued_at": "2021-06-08"},
            self.original,
            b"<html>Ficha</html>",
            PDF_URL,
            {},
        )


def setup_collector(tmp_path, store=None):
    source = SampleSource()
    store = store or LocalStore(tmp_path)
    return Collector(source, None, store), source, store, AsambleaSource.reference("4530")


def test_resume_skips_network_and_refresh_preserves_text_and_versions(tmp_path):
    collector, source, store, ref = setup_collector(tmp_path)
    assert collector.collect(ref)["result"] == "stored"
    text_path = tmp_path / "asamblea/text/2021/asamblea-4530.txt"
    modified = text_path.stat().st_mtime_ns
    state_key = "asamblea/state/asamblea-4530.json"
    first = store.read_json(state_key)
    assert collector.collect(ref)["result"] == "skipped"
    assert source.calls == 1
    assert collector.collect(ref, refresh=True)["result"] == "unchanged"
    assert text_path.stat().st_mtime_ns == modified
    assert store.read_json(state_key)["revision"] == first["revision"]
    assert source.calls == 2


def test_metadata_only_change_creates_revision_and_keeps_old_original(tmp_path):
    collector, source, store, ref = setup_collector(tmp_path)
    collector.collect(ref)
    first = store.read_json("asamblea/state/asamblea-4530.json")
    source.title = "TITULO CORREGIDO"
    collector.collect(ref, refresh=True)
    second = store.read_json("asamblea/state/asamblea-4530.json")
    assert first["revision"] != second["revision"]
    assert first["original_sha256"] == second["original_sha256"]
    assert store.exists(first["version_artifacts"]["original"])
    assert store.exists(second["version_artifacts"]["original"])
    assert second["title"] == source.title


def test_ocr_candidate_removes_stale_indexable_text_but_keeps_partial_archive(tmp_path):
    collector, source, store, ref = setup_collector(tmp_path)
    collector.collect(ref)
    source.original = pdf_bytes(blank=True)
    collector.collect(ref, refresh=True)
    state = store.read_json("asamblea/state/asamblea-4530.json")
    assert state["status"] == "needs_ocr" and not state["indexable"]
    assert "text" not in state["artifacts"]
    assert not store.exists("asamblea/text/2021/asamblea-4530.txt")
    assert store.exists(state["version_artifacts"]["text"])
    assert collector.collect(ref)["result"] == "skipped"


def test_failed_publication_is_repaired_and_archive_manifest_is_immutable(tmp_path):
    class FailingOnceStore(LocalStore):
        fail = True

        def put(self, key, data, content_type):
            if self.fail and key.startswith("asamblea/text/"):
                self.fail = False
                raise OSError("simulated disk interruption")
            return super().put(key, data, content_type)

    store = FailingOnceStore(tmp_path)
    collector, source, store, ref = setup_collector(tmp_path, store)
    with pytest.raises(OSError):
        collector.collect(ref)
    assert store.read_json("asamblea/state/asamblea-4530.json")["status"] == "failed"
    archive_path = next(tmp_path.glob("asamblea/versions/*/*/metadata.json"))
    archived = archive_path.read_bytes()
    assert collector.collect(ref)["status"] == "ready"
    assert source.calls == 2
    assert archive_path.read_bytes() == archived


def test_missing_artifact_triggers_repair(tmp_path):
    collector, source, store, ref = setup_collector(tmp_path)
    collector.collect(ref)
    store.delete("asamblea/pages/2021/asamblea-4530.json")
    assert collector.collect(ref)["result"] == "stored"
    assert source.calls == 2


def test_extraction_failure_archives_download_and_run_continues(tmp_path):
    collector, source, store, ref = setup_collector(tmp_path)
    source.original = b"not a valid PDF"
    report = collector.run([ref, AsambleaSource.reference("6108")])
    assert report["failed"] == 2 and report["status"] == "failed"
    state = store.read_json("asamblea/state/asamblea-4530.json")
    assert state["status"] == "failed"
    assert store.exists(state["archived_original_key"])
    assert store.read_json(report["report_key"])["failed"] == 2


def test_discovery_failure_records_failed_run(tmp_path):
    collector, source, store, ref = setup_collector(tmp_path)

    def failing_discovery():
        yield ref
        raise ValueError("year failed")

    report = collector.run(failing_discovery())
    assert report["stored"] == 1 and report["status"] == "failed"
    assert report["discovery_error"] == "year failed"


@pytest.mark.parametrize("key", ["../escape", "/absolute", "a/../b", "a//b", "a\\b", ""])
def test_storage_rejects_unsafe_keys(key):
    with pytest.raises(ValueError):
        checked_key(key)


def s3_client():
    return boto3.client(
        "s3", region_name="us-east-1", aws_access_key_id="testing", aws_secret_access_key="testing"
    )


def test_s3_paths_and_json_roundtrip():
    client = s3_client()
    store = S3Store("test-corpus", "legislation", client)
    key = "asamblea/state/asamblea-4530.json"
    full_key = "legislation/" + key
    data = json_bytes({"status": "ready"})
    with Stubber(client) as stub:
        stub.add_response(
            "put_object",
            {},
            {
                "Bucket": "test-corpus",
                "Key": full_key,
                "Body": data,
                "ContentType": "application/json",
            },
        )
        stub.add_response(
            "get_object",
            {"Body": StreamingBody(BytesIO(data), len(data))},
            {"Bucket": "test-corpus", "Key": full_key},
        )
        stub.add_response("head_object", {}, {"Bucket": "test-corpus", "Key": full_key})
        store.put(key, data, "application/json")
        assert store.read_json(key) == {"status": "ready"}
        assert store.exists(key)
        assert store.object_key(key) == full_key
        stub.assert_no_pending_responses()


def test_s3_missing_is_distinct_from_permission_failure():
    client = s3_client()
    store = S3Store("test-corpus", client=client)
    expected = {"Bucket": "test-corpus", "Key": "legislation/missing.json"}
    with Stubber(client) as stub:
        stub.add_client_error(
            "get_object",
            service_error_code="NoSuchKey",
            http_status_code=404,
            expected_params=expected,
        )
        stub.add_client_error(
            "head_object",
            service_error_code="AccessDenied",
            http_status_code=403,
            expected_params=expected,
        )
        assert store.read_json("missing.json") is None
        with pytest.raises(ClientError):
            store.exists("missing.json")


def test_s3_pipeline_uses_full_object_keys_and_resumes(tmp_path):
    class MemoryS3:
        objects = None

        def __init__(self):
            self.objects = {}

        def get_object(self, *, Bucket, Key):
            if Key not in self.objects:
                raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
            data = self.objects[Key]
            return {"Body": StreamingBody(BytesIO(data), len(data))}

        def put_object(self, *, Bucket, Key, Body, ContentType):
            assert Key.startswith("legislation/asamblea/")
            self.objects[Key] = Body

        def head_object(self, *, Bucket, Key):
            if Key not in self.objects:
                raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
            return {}

        def delete_object(self, *, Bucket, Key):
            self.objects.pop(Key, None)

    client = MemoryS3()
    store = S3Store("corpus", client=client)
    collector, source, _, ref = setup_collector(tmp_path, store)
    collector.collect(ref)
    state = store.read_json("asamblea/state/asamblea-4530.json")
    assert state["bucket"] == "corpus"
    assert state["artifacts"]["original"] == "legislation/asamblea/files/2021/asamblea-4530.PDF"
    assert all(key in client.objects for key in state["version_artifacts"].values())
    assert collector.collect(ref)["result"] == "skipped"
    assert source.calls == 1


def test_cli_local_collection_and_resume(tmp_path, monkeypatch, capsys):
    from backend.app.jobs import scrape_legislation

    ref = AsambleaSource.reference("4530")
    client = FixtureClient({ref.url: (FIXTURES / "detail.html").read_bytes(), PDF_URL: pdf_bytes()})
    monkeypatch.setattr(scrape_legislation, "HttpClient", lambda *args, **kwargs: client)
    args = ["--document-ids", "4530", "--output", str(tmp_path)]
    assert scrape_legislation.main(args) == 0
    assert (tmp_path / "legislation/asamblea/text/2021/asamblea-4530.txt").exists()
    assert scrape_legislation.main(args) == 0
    assert len(client.calls) == 2
    assert '"skipped": 1' in capsys.readouterr().out
