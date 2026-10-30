from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, unquote, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from .models import DocumentRef, FetchedDocument
from .storage import json_bytes

BASE = "https://www.jurisprudencia.gob.sv"
RESULTS_URL = BASE + "/busqueda/result.php"
RESULT_LIMIT = 300  # Largest result limit offered by the public search UI.
MIN_DATE = date(1753, 1, 1)  # Verified accepted bound; 0001 triggers a query error.
HOSTS = {"www.jurisprudencia.gob.sv", "jurisprudencia.gob.sv"}
MONTHS = {
    m: n
    for n, m in enumerate(
        [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ],
        1,
    )
}


def label(value: str) -> str:
    return " ".join(
        "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))
        .lower()
        .strip(" :")
        .split()
    )


def positive_id(value: str) -> str:
    if not re.fullmatch(r"[0-9]+", value) or int(value) < 1:
        raise ValueError("Portal judicial IDs must be positive integers")
    return str(int(value))


def source_url(value: str, relative_to=BASE + "/busqueda/") -> str:
    parsed = urlsplit(urljoin(relative_to, value))
    if (
        parsed.hostname not in HOSTS
        or parsed.scheme not in ("http", "https")
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 80, 443)
    ):
        raise ValueError("Judicial URL outside source allowlist")
    return urlunsplit(("https", "www.jurisprudencia.gob.sv", parsed.path, parsed.query, ""))


def fiche_reference(value: str) -> DocumentRef:
    url = source_url(value)
    parsed = urlsplit(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if query.get("bd") != ["2"] or any(len(v) != 1 for v in query.values()):
        raise ValueError("Only the legislation catalog (bd=2) is supported")
    if parsed.path == "/busqueda/showExtractos.php":
        note, parent = (
            positive_id(query.get("nota", [""])[0]),
            positive_id(query.get("doc", [""])[0]),
        )
        return DocumentRef(
            f"reform-{note}-{parent}",
            BASE
            + "/busqueda/showExtractos.php?"
            + urlencode({"bd": 2, "nota": note, "doc": parent, "singlePage": "false"}),
        )
    if parsed.path != "/busqueda/showFile.php":
        raise ValueError("Expected a showFile.php or showExtractos.php legislation URL")
    source_id = positive_id(query.get("number", [""])[0])
    kept = {
        "bd": "2",
        **{k: query[k][0] for k in ("data", "fecha", "numero") if k in query},
        "number": source_id,
        "singlePage": "false",
    }
    return DocumentRef(source_id, BASE + "/busqueda/showFile.php?" + urlencode(kept))


def parse_date(value: str | None) -> str | None:
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").date().isoformat() if value else None
    except ValueError:
        return None


def caption_dates(text: str) -> list[str]:
    dates = []
    for day, month, year in re.findall(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", text.lower()):
        try:
            dates.append(date(int(year), MONTHS[month], int(day)).isoformat())
        except (KeyError, ValueError):
            continue
    return dates


def fiche_fields(soup) -> dict[str, str]:
    fields = {}
    for row in soup.select("table tr"):
        cells = row.find_all(["td", "th"], recursive=False)
        if len(cells) == 2 and cells[0].find("b"):
            fields[label(cells[0].get_text(" ", strip=True))] = cells[1].get_text(" ", strip=True)
    # Reform fiches use a list of label/value lines, not the main fiche table.
    for ul in soup.select("#menu2 ul"):
        for line in ul.get_text("\n", strip=True).splitlines():
            key, separator, value = line.partition(":")
            if separator:
                fields[label(key)] = value.strip()
    return fields


def asset_url(soup, fiche_url: str) -> str | None:
    found = []
    for frame in soup.select("iframe[src]"):
        src = frame["src"].strip()
        if not src:
            continue
        target = source_url(src, fiche_url)
        params = parse_qs(urlsplit(target).query)
        files = params.get("File", params.get("file", []))
        if files:
            target = source_url(files[0], target)
        path = unquote(urlsplit(target).path)
        if path.startswith("/DocumentosBoveda/") and path.lower().endswith(
            (".pdf", ".html", ".htm")
        ):
            if ".." in path.split("/") or "\\" in path:
                raise ValueError("Invalid normative asset path")
            found.append(target)
    unique = list(dict.fromkeys(found))
    if len(unique) > 1:
        raise ValueError("Fiche has multiple normative assets; inspect source layout")
    return unique[0] if unique else None


class PortalJudicialSource:
    """Collect legislation (database 2), preserving reported status and reforms."""

    name = "portal_judicial"
    allowed_hosts = HOSTS
    supports_html = True

    @staticmethod
    def reference(source_id: str) -> DocumentRef:
        if source_id.startswith(("https://", "http://")):
            return fiche_reference(source_id)
        reform = re.fullmatch(r"reform-([0-9]+)-([0-9]+)", source_id)
        if reform:
            return fiche_reference(
                BASE
                + "/busqueda/showExtractos.php?"
                + urlencode({"bd": 2, "nota": reform[1], "doc": reform[2]})
            )
        source_id = positive_id(source_id)
        return fiche_reference(
            BASE + "/busqueda/showFile.php?" + urlencode({"bd": 2, "number": source_id})
        )

    def _query(self, client, start: date | None, end: date | None) -> list[DocumentRef]:
        data = {
            "avanzada": "true",
            "baseDatos": 2,
            "nivel1": -1,
            "nivel2": -1,
            "nivel3": -1,
            "nivel4": -1,
            "maximo": RESULT_LIMIT,
            "inicio": start.isoformat() if start else -1,
            "fin": end.isoformat() if end else -1,
            "numeroReferencia": -1,
            "nombreDocumento": -1,
            "propiedades": "",
        }
        response = client.post(RESULTS_URL, data=data)
        soup = BeautifulSoup(response.body, "html.parser")
        table = soup.select_one("table#files")
        if table is None:
            raise ValueError("Judicial search layout/error: missing #files table")
        refs = []
        for row in table.select("tbody > tr"):
            link = row.select_one('a[href*="showFile.php"]')
            if link is None:
                raise ValueError("Unexpected judicial result row without a fiche link")
            ref = fiche_reference(urljoin(RESULTS_URL, link["href"]))
            query = parse_qs(urlsplit(ref.url).query)
            if not query.get("data"):
                raise ValueError("Judicial catalog fiche is missing its normative asset path")
            published = parse_date(query.get("fecha", [None])[0])
            if start and (not published or not start.isoformat() <= published <= end.isoformat()):
                raise ValueError("Judicial date filter was ignored or returned an undated record")
            refs.append(
                DocumentRef(ref.source_id, ref.url, int(published[:4]) if published else None)
            )
        return refs

    def _range(self, client, start: date, end: date):
        refs = self._query(client, start, end)
        if len(refs) >= RESULT_LIMIT:
            if start == end:
                raise ValueError(
                    f"Judicial result cap reached on {start}; cannot claim complete discovery"
                )
            middle = start + (end - start) // 2
            # Query disjoint inclusive ranges; never emit a truncated parent result.
            yield from self._range(client, middle + timedelta(days=1), end)
            yield from self._range(client, start, middle)
        else:
            yield from refs

    def discover(self, client, years: list[int] | None):
        seen = set()
        ranges = (
            [(MIN_DATE, date.today())]
            if years is None
            else [(date(y, 1, 1), date(y, 12, 31)) for y in sorted(set(years), reverse=True)]
        )
        if any(start < MIN_DATE for start, _ in ranges):
            raise ValueError("Judicial publication-year filters start at the verified bound 1753")
        for start, end in ranges:
            for ref in self._range(client, start, end):
                if ref.source_id not in seen:
                    seen.add(ref.source_id)
                    yield ref

    def fetch(self, client, ref: DocumentRef) -> FetchedDocument:
        checked = self.reference(ref.url)
        if checked.source_id != ref.source_id:
            raise ValueError("Fiche URL does not match the requested judicial ID")
        response = client.get(checked.url)
        soup = BeautifulSoup(response.body, "html.parser")
        fields = fiche_fields(soup)
        original_url = asset_url(soup, checked.url)
        is_reform = ref.source_id.startswith("reform-")
        if original_url is None and not is_reform:
            # The direct-ID endpoint exposes database metadata but requires a
            # catalog-provided asset path. Resolve it via bounded publication years.
            issued = parse_date(fields.get("fecha emision"))
            if not issued or "data" in parse_qs(urlsplit(checked.url).query):
                raise ValueError("No normative asset; supply the complete catalog fiche URL")
            year = int(issued[:4])
            resolved = next(
                (
                    r
                    for r in self._range(
                        client, date(year, 1, 1), date(min(year + 1, 9999), 12, 31)
                    )
                    if r.source_id == ref.source_id
                ),
                None,
            )
            if resolved is None:
                raise ValueError(
                    "ID absent from issuance/next-year publication catalogs; supply the complete fiche URL"
                )
            return self.fetch(client, resolved)
        if not fields or original_url is None:
            raise ValueError("Judicial fiche has no metadata or supported PDF/HTML asset")
        query = parse_qs(urlsplit(checked.url).query)
        if is_reform:
            caption = fields.get("nombre", "")
            title = caption
            dates = caption_dates(caption)
            issued = dates[0] if dates else None
            published = dates[-1] if len(dates) >= 2 and "publicado" in caption.lower() else None
            number = fields.get("n° del documento")
            parent_id = f"{self.name}-{query['doc'][0]}"
            gazette = re.search(r"diario oficial\s+no\.?\s*(\d+)", caption, re.IGNORECASE)
            volume = re.search(r"tomo\s+(\d+)", caption, re.IGNORECASE)
        else:
            title = fields.get("nombre") or query.get("numero", [""])[0].replace("=", " ")
            issued = parse_date(fields.get("fecha emision"))
            published = parse_date(fields.get("fecha de publicacion en d. o.")) or parse_date(
                query.get("fecha", [None])[0]
            )
            number = fields.get("numero de decreto o acuerdo")
            parent_id, gazette, volume = None, None, None
        if not title:
            raise ValueError("Judicial fiche has no title")
        related = []
        for link in soup.select('a[href*="showExtractos.php"]'):
            child = fiche_reference(urljoin(checked.url, link["href"]))
            child_query = parse_qs(urlsplit(child.url).query)
            if child_query["doc"][0] != ref.source_id:
                raise ValueError("Reform relation points to a different parent")
            if child.source_id not in {r.source_id for r in related}:
                related.append(child)
        metadata = {
            "title": title,
            "document_type": "reform" if is_reform else "legislation",
            "source_document_type": fields.get("tipo de documento"),
            "decree_number": number,
            "issued_at": issued,
            "published_at": published,
            "official_gazette_number": gazette[1] if gazette else None,
            "official_gazette_volume": volume[1] if volume else fields.get("n° tomo"),
            "source_legal_status": fields.get("vigencia"),
            "legal_status": "unverified",
            "subject": fields.get("materia[legislacion]"),
            "origin": fields.get("origen"),
            "summary": fields.get("consideraciones sobre el documento"),
            "source_fields": fields,
            "related_document_ids": [f"{self.name}-{r.source_id}" for r in related],
        }
        if parent_id:
            metadata.update(
                parent_id=parent_id, relationship="reform_of", relationship_source="portal_fiche"
            )
        original = client.get(original_url)
        original_format = "pdf" if urlsplit(original_url).path.lower().endswith(".pdf") else "html"
        snapshot = {
            "fiche_url": checked.url,
            "source_fields": fields,
            "asset_url": original_url,
            "related_fiche_urls": [r.url for r in related],
        }
        return FetchedDocument(
            ref,
            metadata,
            original.body,
            json_bytes(snapshot),
            original.url,
            {
                k.lower(): v
                for k, v in original.headers.items()
                if k.lower() in ("content-type", "etag", "last-modified")
            },
            detail_format="json",
            original_format=original_format,
            related_documents=related,
        )
