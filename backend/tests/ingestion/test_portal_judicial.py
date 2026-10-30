from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from backend.app.ingestion import portal_judicial as portal
from backend.app.ingestion.extraction import extract_html
from backend.app.ingestion.http import Response
from backend.app.ingestion.pipeline import Collector
from backend.app.ingestion.storage import LocalStore
from backend.app.jobs import scrape_legislation
from backend.tests.ingestion.test_collector import pdf_bytes

FIXTURES = Path(__file__).parent / "fixtures"
FICHE_URL = (
    portal.BASE
    + "/busqueda/showFile.php?bd=2&data=DocumentosBoveda%2FD%2F2%2F2020-2029%2F2021%2F06%2FE75F3.PDF&number=947699&fecha=09%2F06%2F2021&numero=LEY%3DBITCOIN"
)
REF = portal.fiche_reference(FICHE_URL)
PDF_URL = portal.BASE + "/DocumentosBoveda/D/2/2020-2029/2021/06/E75F3.PDF"
REFORM = portal.PortalJudicialSource.reference("reform-1081526-947699")
HTML_URL = portal.BASE + "/DocumentosBoveda/R/2/2020-2029/2021/06/1080B6.HTML"
HTML = b"<html><body><h1>Decreto 199</h1><p>Articulo 1. Texto normativo de prueba para extraccion.</p><p>Articulo 2. Otra disposicion.</p></body></html>"


def result_table(refs):
    return (
        '<table id="files"><tbody>'
        + "".join(f'<tr><td>1</td><td><a href="{r.url}">Documento</a></td></tr>' for r in refs)
        + "</tbody></table>"
    ).encode()


class Client:
    def __init__(self):
        self.calls = []
        self.fiche = (FIXTURES / "judicial_fiche.html").read_bytes()
        self.bodies = {
            REF.url: self.fiche,
            PDF_URL: pdf_bytes(),
            REFORM.url: (FIXTURES / "judicial_reform.html").read_bytes(),
            HTML_URL: HTML,
        }
        self.records = [REF]

    def get(self, url):
        self.calls.append(("GET", url))
        return Response(url, self.bodies[url], {}, 200)

    def post(self, url, *, data):
        self.calls.append(("POST", data.copy()))
        records = [
            r
            for r in self.records
            if data["inicio"]
            <= portal.parse_date(parse_qs(urlsplit(r.url).query)["fecha"][0])
            <= data["fin"]
        ]
        return Response(url, result_table(records[: data["maximo"]]), {}, 200)

    def close(self):
        pass


def test_pdf_fiche_preserves_source_status_without_endorsing_current_validity():
    fetched = portal.PortalJudicialSource().fetch(Client(), REF)
    assert fetched.original_format == "pdf"
    assert fetched.metadata["title"] == "LEY BITCOIN"
    assert fetched.metadata["decree_number"] == "57"
    assert fetched.metadata["issued_at"] == "2021-06-08"
    assert fetched.metadata["published_at"] == "2021-06-09"
    assert fetched.metadata["official_gazette_volume"] == "431"
    assert fetched.metadata["source_legal_status"] == "Vigente"
    assert fetched.metadata["legal_status"] == "unverified"
    assert fetched.related_documents == [REFORM]


def test_html_reform_uses_own_dates_and_numbers_instead_of_parent_fields():
    fetched = portal.PortalJudicialSource().fetch(Client(), REFORM)
    assert fetched.original_format == "html"
    assert fetched.original_url == HTML_URL
    assert fetched.metadata["decree_number"] == "199"
    assert fetched.metadata["issued_at"] == "2025-01-29"
    assert fetched.metadata["published_at"] == "2025-01-30"
    assert fetched.metadata["official_gazette_number"] == "21"  # Not the parent label 110.
    assert fetched.metadata["official_gazette_volume"] == "446"
    assert fetched.metadata["parent_id"] == "portal_judicial-947699"
    assert fetched.metadata["relationship"] == "reform_of"


def test_snapshot_ignores_dynamic_page_chrome():
    client = Client()
    source = portal.PortalJudicialSource()
    first = source.fetch(client, REF)
    client.bodies[REF.url] += (
        b'<div data-cfemail="randomized">contact email</div><script>random_token</script>'
    )
    second = source.fetch(client, REF)
    assert second.detail_html == first.detail_html
    assert second.metadata == first.metadata


def test_direct_numeric_id_resolves_via_catalog_not_guessed_file_paths():
    client = Client()
    direct = portal.PortalJudicialSource.reference("947699")
    client.bodies[direct.url] = client.fiche.replace(
        b"/web/viewer.html?File=https%3A%2F%2Fwww.jurisprudencia.gob.sv%2FDocumentosBoveda%2FD%2F2%2F2020-2029%2F2021%2F06%2FE75F3.PDF",
        b"/web/viewer.html?File=https%3A%2F%2Fwww.jurisprudencia.gob.sv%2F",
    )
    fetched = portal.PortalJudicialSource().fetch(client, direct)
    assert fetched.original_url == PDF_URL
    assert any(method == "POST" for method, _ in client.calls)


def test_discovery_publication_year_filter_and_explicit_empty_result():
    source, client = portal.PortalJudicialSource(), Client()
    assert [r.source_id for r in source.discover(client, [2021])] == ["947699"]
    assert list(source.discover(client, [2020])) == []
    query = client.calls[0][1]
    assert query["baseDatos"] == 2 and query["maximo"] == 300
    assert query["inicio"] == "2021-01-01" and query["fin"] == "2021-12-31"


def test_saturated_ranges_split_without_emitting_truncated_parent_results(monkeypatch):
    monkeypatch.setattr(portal, "RESULT_LIMIT", 2)
    client = Client()
    client.records = [
        portal.fiche_reference(
            portal.BASE
            + "/busqueda/showFile.php?bd=2&number="
            + str(n)
            + "&fecha="
            + day
            + "&data=DocumentosBoveda/D/2/2021/AA.PDF"
        )
        for n, day in [(1, "01/01/2021"), (2, "01/12/2021"), (3, "02/12/2021")]
    ]
    refs = list(portal.PortalJudicialSource().discover(client, [2021]))
    assert sorted(r.source_id for r in refs) == ["1", "2", "3"]
    assert len(client.calls) > 1


def test_saturated_single_day_fails_instead_of_claiming_complete_discovery(monkeypatch):
    monkeypatch.setattr(portal, "RESULT_LIMIT", 1)
    with pytest.raises(ValueError, match="result cap"):
        list(portal.PortalJudicialSource()._range(Client(), date(2021, 6, 9), date(2021, 6, 9)))


def test_ignored_date_filter_or_error_response_fails():
    class IgnoringClient(Client):
        def post(self, url, *, data):
            return Response(url, result_table([REF]), {}, 200)

    with pytest.raises(ValueError, match="filter was ignored"):
        list(portal.PortalJudicialSource().discover(IgnoringClient(), [2020]))

    class ErrorClient(Client):
        def post(self, url, *, data):
            return Response(url, b"Ha ocurrido un error inesperado en la consulta.", {}, 200)

    with pytest.raises(ValueError, match="missing #files"):
        list(portal.PortalJudicialSource().discover(ErrorClient(), [2021]))


def test_all_years_uses_supported_sql_date_range():
    client = Client()
    list(portal.PortalJudicialSource().discover(client, None))
    assert client.calls[0][1]["inicio"] == "1753-01-01"
    with pytest.raises(ValueError, match="1753"):
        list(portal.PortalJudicialSource().discover(Client(), [1600]))


@pytest.mark.parametrize(
    "url",
    [
        "https://other.invalid/busqueda/showFile.php?bd=2&number=1",
        portal.BASE + "/busqueda/showFile.php?bd=1&number=1",
        portal.BASE + "/busqueda/showFile.php?bd=2&number=1&number=2",
        portal.BASE + "/busqueda/showFile.php?bd=2&number=../1",
        portal.BASE + "/busqueda/other.php?bd=2&number=1",
    ],
)
def test_fiche_reference_rejects_unsupported_or_ambiguous_urls(url):
    with pytest.raises(ValueError):
        portal.PortalJudicialSource.reference(url)


def test_asset_urls_are_not_allowed_to_escape_source_or_boveda():
    from bs4 import BeautifulSoup

    with pytest.raises(ValueError, match="allowlist"):
        portal.asset_url(
            BeautifulSoup('<iframe src="https://other.invalid/x.pdf">', "html.parser"), REF.url
        )
    assert (
        portal.asset_url(
            BeautifulSoup('<iframe src="/DocumentosBoveda/../private.pdf">', "html.parser"), REF.url
        )
        is None
    )


def test_html_extraction_uses_segments_not_fabricated_pdf_pages():
    result = extract_html(HTML.replace(b"</body>", b"<script>do not index this</script></body>"))
    assert result["status"] == "ready"
    assert result["page_count"] == 0 and result["pages"] == []
    assert "do not index this" not in result["text"]
    assert len(result["segments"]) == 3
    for segment in result["segments"]:
        assert result["text"][segment["start"] : segment["end"]] == segment["text"]
    with pytest.raises(ValueError, match="insufficient"):
        extract_html(b"<html>Empty</html>")


def test_html_error_pages_are_not_indexable_normative_documents():
    with pytest.raises(ValueError, match="error or browser"):
        extract_html(
            b"<html><head><title>Just a moment</title></head><body><p>Checking your browser. Please enable JavaScript and cookies to continue.</p></body></html>"
        )


def test_html_encoding_and_hidden_content():
    html = (
        '<html><head><meta charset="windows-1252"><style>.a { color:red; }</style></head><body>'
        "<p>Artículo primero: disposición pública con suficiente texto normativo.</p>"
        '<div hidden><b>hidden text</b></div><p style="display: none">another hidden text</p>'
        "</body></html>"
    ).encode("windows-1252")
    result = extract_html(html)
    assert "Artículo primero" in result["text"]
    assert "hidden text" not in result["text"]


def test_pdf_bytes_are_not_accepted_as_html():
    with pytest.raises(ValueError, match="received PDF"):
        extract_html(pdf_bytes())


def test_html_original_bytes_and_storage_content_type_are_preserved(tmp_path):
    class RecordingStore(LocalStore):
        def put(self, key, data, content_type):
            if key.endswith(".HTML"):
                assert content_type == "text/html"
            return super().put(key, data, content_type)

    client, store = Client(), RecordingStore(tmp_path)
    client.bodies[HTML_URL] = (
        '<meta charset="windows-1252"><p>Artículo primero: disposición pública con suficiente texto normativo.</p>'
    ).encode("windows-1252")
    collector = Collector(portal.PortalJudicialSource(), client, store)
    collector.collect(REFORM)
    state = store.read_json("portal_judicial/state/portal_judicial-reform-1081526-947699.json")
    assert (tmp_path / state["artifacts"]["original"]).read_bytes() == client.bodies[HTML_URL]
    assert "Artículo primero" in (tmp_path / state["artifacts"]["text"]).read_text()


def test_parent_and_reform_are_stored_and_resumed_independently(tmp_path):
    source, client, store = portal.PortalJudicialSource(), Client(), LocalStore(tmp_path)
    collector = Collector(source, client, store)
    assert collector.run([REF], limit=1)["stored"] == 1
    assert not store.exists("portal_judicial/state/portal_judicial-reform-1081526-947699.json")
    second = collector.run([REF], limit=2)
    assert second["skipped"] == 1 and second["stored"] == 1
    state = store.read_json("portal_judicial/state/portal_judicial-reform-1081526-947699.json")
    assert state["original_format"] == "html"
    assert state["artifacts"]["original"].endswith(
        "/2025/portal_judicial-reform-1081526-947699.HTML"
    )
    pages = store.read_json(state["artifacts"]["pages"])
    assert pages["page_count"] == 0 and pages["segments"]
    third = collector.run([REF], refresh=True)
    assert third["unchanged"] == 2
    assert collector.run([REF])["skipped"] == 2


def test_related_document_failure_does_not_erase_parent_success(tmp_path):
    source, client, store = portal.PortalJudicialSource(), Client(), LocalStore(tmp_path)
    client.bodies[HTML_URL] = b"<html>Empty</html>"
    collector = Collector(source, client, store)
    report = collector.run([REF])
    assert report["stored"] == 1 and report["failed"] == 1
    assert store.read_json("portal_judicial/state/portal_judicial-947699.json")["status"] == "ready"
    client.bodies[HTML_URL] = HTML
    report = collector.run([REF])
    assert report["skipped"] == 1 and report["stored"] == 1


def test_cli_portal_collects_pdf_and_related_html(tmp_path, monkeypatch):
    client = Client()
    monkeypatch.setattr(scrape_legislation, "HttpClient", lambda *args, **kwargs: client)
    assert (
        scrape_legislation.main(
            [
                "--source",
                "portal_judicial",
                "--document-ids",
                REF.url,
                "--limit",
                "2",
                "--output",
                str(tmp_path),
            ]
        )
        == 0
    )
    root = tmp_path / "legislation/portal_judicial"
    assert (root / "files/2021/portal_judicial-947699.PDF").exists()
    assert (root / "files/2025/portal_judicial-reform-1081526-947699.HTML").exists()
