from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from .models import DocumentRef, FetchedDocument

BASE = "https://www.asamblea.gob.sv"
INDEX_PATH = "/leyes-y-decretos/decretos-por-anios"
DETAIL_RE = re.compile(r"^/leyes-y-decretos/view/(\d+)/?$")


def normalize(value: str) -> str:
    return " ".join(
        "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))
        .lower()
        .strip(" :")
        .split()
    )


def content(html: bytes):
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("#asamblea-contenido")
    if main is None:
        raise ValueError("Asamblea layout changed: missing #asamblea-contenido")
    return main


def parse_date(value: str | None) -> str | None:
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").date().isoformat() if value else None
    except ValueError:
        return None


class AsambleaSource:
    name = "asamblea"
    allowed_hosts = {"www.asamblea.gob.sv", "asamblea.gob.sv"}
    extra_ca_file = Path(__file__).parent / "certs" / "sectigo-ov-r36.pem"

    @staticmethod
    def reference(source_id: str) -> DocumentRef:
        if not source_id.isascii() or not source_id.isdigit():
            raise ValueError("Asamblea source IDs must be numeric")
        source_id = str(int(source_id))
        return DocumentRef(source_id, f"{BASE}/leyes-y-decretos/view/{source_id}")

    def discover(self, client, years: list[int] | None):
        if years is None:
            main = content(client.get(BASE + INDEX_PATH).body)
            years = sorted(
                {
                    int(match.group(1))
                    for a in main.select("a[href]")
                    if (
                        match := re.fullmatch(
                            INDEX_PATH + r"/(\d{4})/0/?", urlsplit(urljoin(BASE, a["href"])).path
                        )
                    )
                },
                reverse=True,
            )
            if not years:
                raise ValueError("Asamblea year index contains no years")
        seen_documents = set()
        for year in sorted(set(years), reverse=True):
            pending = [f"{BASE}{INDEX_PATH}/{year}/0"]
            seen_pages = set()
            while pending:
                url = pending.pop(0)
                if url in seen_pages:
                    continue
                seen_pages.add(url)
                if len(seen_pages) > 1000:
                    raise ValueError(f"Too many catalog pages for {year}")
                main = content(client.get(url).body)
                found = 0
                for a in main.select("[data-al-modal-url], a[href]"):
                    parts = a.get("data-al-modal-url", a.get("href", "")).split()
                    if not parts:
                        continue
                    target = parts[0]
                    target = urljoin(url, target)
                    match = DETAIL_RE.fullmatch(urlsplit(target).path)
                    if match:
                        client.validate_url(target)
                        found += 1
                        source_id = match.group(1)
                        if source_id not in seen_documents:
                            seen_documents.add(source_id)
                            yield DocumentRef(source_id, target, year)
                if not found and not re.search(
                    r"no se encontraron|sin resultados|no existen", main.get_text(), re.I
                ):
                    raise ValueError(
                        f"No document links found for {year}; inspect source layout/year"
                    )
                for a in main.select('.pager a[href], a[rel="next"], .pagination a[href]'):
                    target = urljoin(url, a["href"])
                    if urlsplit(target).path.startswith(f"{INDEX_PATH}/{year}/"):
                        client.validate_url(target)
                        pending.append(target)

    def fetch(self, client, ref: DocumentRef) -> FetchedDocument:
        response = client.get(ref.url)
        main = content(response.body)
        title = main.select_one("h1")
        if not title or not title.get_text(strip=True):
            raise ValueError(f"Missing document title: {ref.url}")
        fields = {}
        for row in main.select("tr"):
            for th in row.select("th"):
                td = th.find_next_sibling("td")
                if td:
                    fields[normalize(th.get_text(" ", strip=True))] = td.get_text(" ", strip=True)
        # Publication metadata uses column headers, unlike the first table.
        for table in main.select("table"):
            headers = table.select("thead th")
            values = table.select("tbody tr:first-child td")
            if headers and len(headers) == len(values):
                fields.update(
                    {
                        normalize(h.get_text(" ", strip=True)): v.get_text(" ", strip=True)
                        for h, v in zip(headers, values)
                    }
                )
        links = list(
            dict.fromkeys(
                urljoin(response.url, a["href"])
                for a in main.select("a[href]")
                if urlsplit(a["href"]).path.lower().endswith(".pdf")
            )
        )
        if len(links) != 1:
            raise ValueError(f"Expected one PDF link, found {len(links)}: {ref.url}")
        summary = None
        for card in main.select(".card"):
            header = card.select_one(".card-header")
            body = card.select_one(".card-body")
            if header and normalize(header.get_text()) == "resumen" and body:
                summary = body.get_text(" ", strip=True)
        document_type = "unknown"
        for header in main.select(".card-header"):
            label = normalize(header.get_text())
            if label == "datos de la ley":
                document_type = "law"
            elif label == "datos del decreto":
                document_type = "decree"
        metadata = {
            "title": title.get_text(" ", strip=True),
            "document_type": document_type,
            "decree_number": fields.get("numero del decreto"),
            "issued_at": parse_date(fields.get("fecha de emision")),
            "published_at": parse_date(fields.get("fecha de publicacion")),
            "official_gazette_number": fields.get("no. diario oficial"),
            "official_gazette_volume": fields.get("numero de tomo"),
            "subject": fields.get("materia"),
            "sub_subject": fields.get("sub-materia"),
            "legal_branch": fields.get("rama del derecho"),
            "summary": summary,
            "source_fields": fields,
            "legal_status": "unverified",
        }
        original = client.get(links[0])
        return FetchedDocument(
            ref,
            metadata,
            original.body,
            response.body,
            original.url,
            {
                k.lower(): v
                for k, v in original.headers.items()
                if k.lower() in ("etag", "last-modified", "content-type")
            },
        )
