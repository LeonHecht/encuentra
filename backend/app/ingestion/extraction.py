from __future__ import annotations

import re
from io import BytesIO

from bs4 import BeautifulSoup
from pypdf import PdfReader, __version__

EXTRACTOR_VERSION = f"pypdf-{__version__}-pages-v1"
HTML_EXTRACTOR_VERSION = "html-visible-blocks-v1"


def extract_pdf(data: bytes, min_page_characters: int = 20) -> dict:
    offset = data.find(b"%PDF-")
    if offset < 0 or offset > 1024:
        raise ValueError("Download is not a PDF")
    # Some Asamblea files have an 8-byte prefix. Keep original bytes in storage.
    reader = PdfReader(BytesIO(data[offset:]), strict=False)
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError("PDF needs an opening password")
    if not reader.pages:
        raise ValueError("PDF contains no pages")
    pages, offset_in_text = [], 0
    for number, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").replace("\x00", "")
        if pages:
            offset_in_text += 2  # The separator in the complete text is two newlines.
        pages.append(
            {
                "page": number,
                "text": text,
                "start": offset_in_text,
                "end": offset_in_text + len(text),
            }
        )
        offset_in_text += len(text)
    candidates = [p["page"] for p in pages if len(p["text"].strip()) < min_page_characters]
    return {
        "extractor_version": EXTRACTOR_VERSION,
        "pdf_header_offset": offset,
        "page_count": len(pages),
        "ocr_candidate_pages": candidates,
        "status": "needs_ocr" if candidates else "ready",
        "pages": pages,
        "text": "\n\n".join(p["text"] for p in pages),
    }


def extract_html(data: bytes) -> dict:
    if b"%PDF-" in data[:1024]:
        raise ValueError("Expected HTML, received PDF content")
    soup = BeautifulSoup(data, "html.parser")
    if not soup.find(["html", "body", "p", "div", "table", "h1", "pre"]):
        raise ValueError("Expected an HTML document or normative HTML fragment")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if soup.select_one("#challenge-form, #cf-challenge-running, .cf-error-details") or re.search(
        r"not found|access denied|just a moment|^error\b", title, re.IGNORECASE
    ):
        raise ValueError("HTML asset is an error or browser challenge page")
    for tag in soup.select("head, script, style, noscript, template, nav, form"):
        if not tag.decomposed:
            tag.decompose()
    for tag in soup.find_all(True):
        if tag.decomposed:
            continue
        if (
            tag.has_attr("hidden")
            or tag.get("aria-hidden") == "true"
            or re.search(
                r"display\s*:\s*none|visibility\s*:\s*hidden", tag.get("style", ""), re.IGNORECASE
            )
        ):
            tag.decompose()
    root = soup.body or soup
    for br in root.find_all("br"):
        br.replace_with("\n\n")
    for tag in root.find_all(["p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "pre"]):
        tag.insert_before("\n\n")
        tag.insert_after("\n\n")
    blocks = [
        re.sub(r"\s+", " ", t).strip(" \ufeff\x00") for t in re.split(r"\n\s*\n", root.get_text())
    ]
    blocks = [b for b in blocks if b]
    text = "\n\n".join(blocks)
    if len(text) < 40:
        raise ValueError("HTML contains insufficient normative text")
    offset, segments = 0, []
    for number, block in enumerate(blocks, 1):
        segments.append(
            {"segment": number, "text": block, "start": offset, "end": offset + len(block)}
        )
        offset += len(block) + 2
    # HTML has logical segments, not printed PDF pages.
    return {
        "extractor_version": HTML_EXTRACTOR_VERSION,
        "format": "html",
        "page_count": 0,
        "pages": [],
        "segments": segments,
        "ocr_candidate_pages": [],
        "status": "ready",
        "text": text,
    }
