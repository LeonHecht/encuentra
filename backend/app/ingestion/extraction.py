from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader, __version__

EXTRACTOR_VERSION = f"pypdf-{__version__}-pages-v1"


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
