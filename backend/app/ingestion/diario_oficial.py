from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import datetime
from email.message import Message

from bs4 import BeautifulSoup

from .models import DocumentRef, FetchedDocument
from .storage import json_bytes

BASE = "https://www.diariooficial.gob.sv"
MONTHS_URL = BASE + "/api/v1/meses-disponibles"
DOCUMENTS_URL = BASE + "/api/v1/diarios-disponibles"


def numeric_id(value) -> str:
    value = str(value)
    if not re.fullmatch(r"[0-9]+", value) or int(value) < 1:
        raise ValueError("Diario Oficial source IDs must be positive integers")
    return str(int(value))


def iso_date(value) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return None


def filename_date(filename: str | None) -> str | None:
    if not filename or not re.fullmatch(r"\d{2}-\d{2}-\d{4}\.pdf", filename, re.IGNORECASE):
        return None
    try:
        return datetime.strptime(filename[:-4], "%d-%m-%Y").date().isoformat()
    except ValueError:
        return None


def payload(response):
    try:
        return json.loads(response.body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(f"Diario Oficial returned invalid JSON: {response.url}") from exc


class DiarioOficialSource:
    """Archive files/editions, including historical parts; never individual laws."""

    name = "diario_oficial"
    allowed_hosts = {"www.diariooficial.gob.sv", "diariooficial.gob.sv"}

    @staticmethod
    def reference(source_id: str) -> DocumentRef:
        source_id = numeric_id(source_id)
        return DocumentRef(source_id, f"{BASE}/seleccion/{source_id}")

    def discover(self, client, years: list[int] | None, *, months: list[int] | None = None):
        home = BeautifulSoup(client.get(BASE + "/").body, "html.parser")
        options = home.select("select#year option[value]")
        available_years = {
            int(o["value"])
            for o in options
            if re.fullmatch(r"[0-9]{4}", o["value"]) and int(o["value"]) > 0
        }
        if not available_years:
            raise ValueError("Diario Oficial layout changed: no years in #year")
        selected_years = available_years if years is None else set(years)
        if not selected_years <= available_years:
            raise ValueError(
                f"Years absent from Diario Oficial catalog: {sorted(selected_years - available_years)}"
            )
        if months is not None and any(type(m) is not int or not 1 <= m <= 12 for m in months):
            raise ValueError("Months must be integers between 1 and 12")
        seen = set()
        for year in sorted(selected_years, reverse=True):
            values = payload(client.post(MONTHS_URL, data={"year": year}))
            if not isinstance(values, list):
                raise ValueError(f"Unexpected months response for {year}")
            available_months = set()
            for item in values:
                value = item.get("month", item.get("mes")) if isinstance(item, dict) else item
                if not re.fullmatch(r"[0-9]{1,2}", str(value)) or not 1 <= int(value) <= 12:
                    raise ValueError(f"Invalid catalog month for {year}: {item!r}")
                available_months.add(int(value))
            selected_months = available_months if months is None else available_months & set(months)
            for month in sorted(selected_months, reverse=True):
                query = {"year": year, "month": month}
                data = payload(client.post(DOCUMENTS_URL, data=query))
                if not isinstance(data, dict) or not isinstance(data.get("data"), list):
                    raise ValueError(f"Unexpected document response for {year}-{month:02}")
                for row in data["data"]:
                    if (
                        not isinstance(row, dict)
                        or not isinstance(row.get("NombreArchivo"), str)
                        or not row["NombreArchivo"].strip()
                    ):
                        raise ValueError(f"Invalid Diario Oficial catalog record: {row!r}")
                    source_id = numeric_id(row.get("Id"))
                    if source_id not in seen:
                        seen.add(source_id)
                        ref = self.reference(source_id)
                        yield replace(
                            ref, catalog_year=year, catalog_data={"query": query, "record": row}
                        )

    def fetch(self, client, ref: DocumentRef) -> FetchedDocument:
        catalog = ref.catalog_data
        row = catalog.get("record", {})
        query = catalog.get("query", {})
        if catalog and (not isinstance(row, dict) or numeric_id(row.get("Id")) != ref.source_id):
            raise ValueError("Catalog ID does not match the requested Diario Oficial file")
        response = client.get(ref.url)
        header = Message()
        header["Content-Disposition"] = response.headers.get("content-disposition", "")
        header_filename = header.get_filename()
        filename = row.get("NombreArchivo") or header_filename
        catalog_date = iso_date(row.get("FechaInicio"))
        inferred_date = filename_date(filename)
        inexact = str(row.get("FechaInexacta", "")).lower()
        precision = "unknown"
        if catalog_date and inexact in ("0", "false"):
            precision = "day"
        elif catalog_date and inexact in ("1", "true"):
            precision = "approximate"
        # A direct download has no API metadata. A filename may identify a storage
        # year, but is not used to assert an exact legal publication date.
        if ref.catalog_year is None and inferred_date:
            ref = replace(ref, catalog_year=int(inferred_date[:4]))
        metadata = {
            "title": f"Diario Oficial — {filename or 'archivo ' + ref.source_id}",
            "document_type": "official_gazette",
            "document_granularity": "archive_file",
            "source_filename": filename,
            "download_filename": header_filename,
            "issued_at": None,
            "published_at": catalog_date if precision == "day" else None,
            "publication_date_precision": precision,
            "catalog_date": catalog_date,
            "filename_date": inferred_date,
            "official_gazette_number": None,
            "official_gazette_volume": None,
            "legal_status": "unverified",
            "source_fields": row,
            "catalog_url": DOCUMENTS_URL if catalog else None,
            "catalog_query": query,
        }
        snapshot = {
            "catalog_url": metadata["catalog_url"],
            "query": query,
            "record": row,
            "download_url": ref.url,
            "download_filename": header_filename,
        }
        return FetchedDocument(
            ref=ref,
            metadata=metadata,
            original=response.body,
            detail_html=json_bytes(snapshot),
            detail_format="json",
            original_url=response.url,
            response_headers={
                k.lower(): v
                for k, v in response.headers.items()
                if k.lower() in ("etag", "last-modified", "content-type", "content-disposition")
            },
        )
