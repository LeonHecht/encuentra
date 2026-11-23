from html import escape
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from backend.app.core.config import settings
from backend.app.services.case_retrieval import CASE_CITATION_PATH, MAX_CASE_ID_LENGTH, fetch_case

router = APIRouter()


@router.get(CASE_CITATION_PATH, response_class=HTMLResponse, include_in_schema=False)
def supreme_court_citation(
    case_id: Annotated[str, Query(alias="id", min_length=1, max_length=MAX_CASE_ID_LENGTH)],
) -> str:
    if settings.CASE_CITATION_BASE_URL is None:
        raise HTTPException(status_code=404, detail="Citation not found")

    case = fetch_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Citation not found")

    title = escape(case.title)
    year = f" · {case.case_year}" if case.case_year is not None else ""
    excerpt_note = "<p>El texto de la resolución se muestra parcialmente.</p>" if case.truncated else ""
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | Encuentra</title>
</head>
<body>
  <main style="max-width: 48rem; margin: 2rem auto; padding: 0 1rem; font: 1rem/1.6 system-ui, sans-serif">
    <p>Corte Suprema de Justicia de El Salvador{year}</p>
    <h1>{title}</h1>
    <p>ID de la resolución: {escape(case.id)}</p>
    {excerpt_note}
    <article style="white-space: pre-wrap; overflow-wrap: anywhere">{escape(case.text)}</article>
  </main>
</body>
</html>"""
