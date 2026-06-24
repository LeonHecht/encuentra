from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from backend.app.core.config import settings
from backend.app.services.auth import get_supabase
from backend.app.services.search import search_engine


MetadataStatus = Literal["missing", "pending", "ready", "failed"]


class MetadataStoreUnavailable(RuntimeError):
    pass


class CaseParties(BaseModel):
    actors: list[str] = Field(default_factory=list)
    favored_parties: list[str] = Field(default_factory=list)
    defendants_or_authorities: list[str] = Field(default_factory=list)
    other_relevant_parties: list[str] = Field(default_factory=list)


class LegalProvision(BaseModel):
    law: str | None = None
    article: str | None = None
    text_reference: str | None = None


class RelevantDate(BaseModel):
    label: str
    date_text: str | None = None
    iso_date: str | None = None


class MetadataConfidence(BaseModel):
    overall: float = Field(ge=0, le=1)
    notes: str | None = None


class CaseMetadata(BaseModel):
    generated_title: str | None = None
    court_chamber: str | None = None
    resolution_type: str | None = None
    outcome: str | None = None
    parties: CaseParties = Field(default_factory=CaseParties)
    legal_issue_summary: str | None = None
    legal_questions: list[str] = Field(default_factory=list)
    key_legal_provisions: list[LegalProvision] = Field(default_factory=list)
    relevant_dates: list[RelevantDate] = Field(default_factory=list)
    legal_area_tags: list[str] = Field(default_factory=list)
    confidence: MetadataConfidence = Field(default_factory=lambda: MetadataConfidence(overall=0, notes=None))


CASE_METADATA_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "generated_title",
        "court_chamber",
        "resolution_type",
        "outcome",
        "parties",
        "legal_issue_summary",
        "legal_questions",
        "key_legal_provisions",
        "relevant_dates",
        "legal_area_tags",
        "confidence",
    ],
    "properties": {
        "generated_title": {"type": ["string", "null"]},
        "court_chamber": {"type": ["string", "null"]},
        "resolution_type": {"type": ["string", "null"]},
        "outcome": {"type": ["string", "null"]},
        "parties": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "actors",
                "favored_parties",
                "defendants_or_authorities",
                "other_relevant_parties",
            ],
            "properties": {
                "actors": {"type": "array", "items": {"type": "string"}},
                "favored_parties": {"type": "array", "items": {"type": "string"}},
                "defendants_or_authorities": {"type": "array", "items": {"type": "string"}},
                "other_relevant_parties": {"type": "array", "items": {"type": "string"}},
            },
        },
        "legal_issue_summary": {"type": ["string", "null"]},
        "legal_questions": {"type": "array", "items": {"type": "string"}},
        "key_legal_provisions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["law", "article", "text_reference"],
                "properties": {
                    "law": {"type": ["string", "null"]},
                    "article": {"type": ["string", "null"]},
                    "text_reference": {"type": ["string", "null"]},
                },
            },
        },
        "relevant_dates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["label", "date_text", "iso_date"],
                "properties": {
                    "label": {"type": "string"},
                    "date_text": {"type": ["string", "null"]},
                    "iso_date": {"type": ["string", "null"]},
                },
            },
        },
        "legal_area_tags": {"type": "array", "items": {"type": "string"}},
        "confidence": {
            "type": "object",
            "additionalProperties": False,
            "required": ["overall", "notes"],
            "properties": {
                "overall": {"type": "number", "minimum": 0, "maximum": 1},
                "notes": {"type": ["string", "null"]},
            },
        },
    },
}


SYSTEM_PROMPT = """Eres un asistente juridico especializado en resoluciones judiciales salvadorenas.

Extrae metadatos para una tarjeta de resultado de busqueda juridica.

Reglas:
- Usa unicamente la informacion contenida en el documento.
- No inventes datos.
- Si un dato no aparece claramente, usa null o una lista vacia.
- Resume en espanol claro, neutral y profesional.
- No incluyas analisis especulativo.
- Distingue entre hechos del caso, decision procesal y razonamiento juridico.
- Incluye legal_questions como una lista breve de cuestiones juridicas centrales, no como fragmentos textuales.
- Manten generated_title como un titulo util para abogados, no como marketing.
- El ejemplo siguiente es solo una guia de formato y nivel de detalle. No reutilices nombres, fechas, normas, resultados ni partes del ejemplo si no aparecen en el documento analizado.

Ejemplo de calidad esperada:
{
    "generated_title": "Habeas corpus sobre detención provisional por agrupaciones ilícitas",
    "court_chamber": "Sala de lo Constitucional de la Corte Suprema de Justicia",
    "resolution_type": "Habeas corpus / improcedencia",
    "outcome": "Petición declarada improcedente por tratarse de asuntos de mera legalidad que deben ventilarse en la vía ordinaria.",
    "parties": {
        "actors": ["NAAR", "LAMA"],
        "favored_parties": [],
        "defendants_or_authorities": ["Juez 4 del Tribunal Tercero Contra el Crimen Organizado"],
        "other_relevant_parties": []
    },
    "legal_issue_summary": "La Sala declara improcedente el habeas corpus porque el reclamo se refiere a la valoración de indicios y participación dentro del proceso penal ordinario, no a una vulneración constitucional directa de la libertad personal.",
    "legal_questions": [
        "Procedencia del habeas corpus frente a decisiones de detención provisional.",
        "Límites de la revisión constitucional sobre valoración de indicios y participación del imputado."
    ],
    "key_legal_provisions": [
        {"law": "Constitución", "article": "Arts. 11, 12, 13", "text_reference": "Arts. 11, 12, 13 Cn."},
        {"law": "Código Procesal Penal", "article": "Arts. 323, 326, 327, 330", "text_reference": "arts. 323, 326, 327, 330 CPP"}
    ],
    "relevant_dates": [
        {"label": "Resolución de improcedencia", "date_text": "8 de enero de 2025", "iso_date": "2025-01-08"}
    ],
    "legal_area_tags": ["habeas corpus", "libertad personal", "detención provisional", "proceso penal"],
    "confidence": {
        "overall": 0.86,
        "notes": "La información principal aparece en el encabezado y en la parte resolutiva."
    }
}
"""


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_hash(space: str, doc_id: str, text: str) -> str:
    h = hashlib.sha256()
    h.update(space.encode("utf-8"))
    h.update(b"\0")
    h.update(doc_id.encode("utf-8"))
    h.update(b"\0")
    h.update(text.encode("utf-8", errors="ignore"))
    return h.hexdigest()


def get_metadata_row(space: str, doc_id: str) -> dict[str, Any] | None:
    try:
        resp = (
            get_supabase()
            .table("case_metadata")
            .select("*")
            .eq("space", space)
            .eq("doc_id", doc_id)
            .execute()
        )
    except Exception as exc:
        print(f"[case_metadata] Failed to fetch metadata row {space}/{doc_id}: {exc}", flush=True)
        raise MetadataStoreUnavailable(str(exc)) from exc
    return resp.data[0] if resp.data else None


def get_metadata_rows(space: str, doc_ids: list[str]) -> dict[str, dict[str, Any]] | None:
    if not doc_ids:
        return {}
    try:
        resp = (
            get_supabase()
            .table("case_metadata")
            .select("*")
            .eq("space", space)
            .in_("doc_id", doc_ids)
            .execute()
        )
    except Exception as exc:
        print(f"[case_metadata] Failed to fetch metadata rows: {exc}", flush=True)
        return None
    return {row["doc_id"]: row for row in (resp.data or [])}


def normalize_status(row: dict[str, Any] | None) -> MetadataStatus:
    if not row:
        return "missing"
    status = row.get("status")
    if status in ("pending", "ready", "failed"):
        return status
    return "missing"


def row_to_response(space: str, doc_id: str, row: dict[str, Any] | None) -> dict[str, Any]:
    status = normalize_status(row)
    return {
        "space": space,
        "doc_id": doc_id,
        "status": status,
        "metadata": row.get("metadata") if row and status == "ready" else None,
        "error": row.get("error") if row and status == "failed" else None,
    }


def save_metadata_payload(payload: dict[str, Any], retries: int = 3) -> bool:
    doc_ref = f"{payload.get('space')}/{payload.get('doc_id')}"
    for attempt in range(1, retries + 1):
        try:
            get_supabase().table("case_metadata").upsert(payload, on_conflict="space,doc_id").execute()
            return True
        except Exception as exc:
            print(f"[case_metadata] Failed to save metadata row {doc_ref} (attempt {attempt}/{retries}): {exc}", flush=True)
            if attempt < retries:
                time.sleep(0.5 * attempt)
    return False


def should_retry_pending(row: dict[str, Any] | None) -> bool:
    if not row or row.get("status") != "pending":
        return True
    updated_at = row.get("updated_at")
    if not updated_at:
        return True
    try:
        updated = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
    except ValueError:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.CASE_METADATA_PENDING_RETRY_MINUTES)
    return updated < cutoff


def upsert_pending(space: str, doc_id: str, row: dict[str, Any] | None = None) -> bool:
    if row and row.get("status") == "ready":
        return False
    if row and row.get("status") == "failed":
        attempts = int(row.get("attempt_count") or 0)
        if attempts >= settings.CASE_METADATA_MAX_RETRIES:
            return False
    if row and row.get("status") == "pending" and not should_retry_pending(row):
        return False

    attempts = int(row.get("attempt_count") or 0) if row else 0
    payload = {
        "space": space,
        "doc_id": doc_id,
        "status": "pending",
        "error": None,
        "attempt_count": attempts,
        "updated_at": _utcnow_iso(),
    }
    return save_metadata_payload(payload)


def _get_openai_client() -> OpenAI | None:
    if not settings.OPENAI_API_KEY:
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _build_user_prompt(
    *,
    query: str,
    doc_id: str,
    case_year: int | None,
    matched_snippet: str | None,
    full_document_text: str,
) -> str:
    return f"""Consulta del usuario:
{query}

ID del documento:
{doc_id}

Ano inferido:
{case_year or "Desconocido"}

Fragmento encontrado por busqueda:
{matched_snippet or "Desconocido"}

Documento legal completo:
{full_document_text}

Extrae la informacion para la tarjeta de resultado.

Instrucciones especificas:
- Usa el documento completo, no solo el fragmento encontrado.
- Si el documento contiene varias fechas, distingue su funcion: fecha de resolucion, fecha de presentacion, fecha de captura, fecha de acto impugnado, fecha de notificacion, etc.
- Si el documento contiene multiples autoridades o partes, identifica su rol.
- Si el documento no contiene titulo real, genera un titulo descriptivo a partir del tema juridico central.
- Identifica las cuestiones juridicas centrales en legal_questions.
- Si un dato no aparece claramente, usa null o una lista vacia.
- Para el campo 'Resultado', devuelve una frase breve.
"""


def extract_metadata_with_openai(
    *,
    query: str,
    doc_id: str,
    case_year: int | None,
    matched_snippet: str | None,
    full_document_text: str,
) -> CaseMetadata:
    client = _get_openai_client()
    if client is None:
        raise RuntimeError("OpenAI is not configured.")

    response = client.responses.create(
        model=settings.CASE_METADATA_MODEL,
        reasoning={"effort": settings.CASE_METADATA_REASONING_EFFORT},
        instructions=SYSTEM_PROMPT,
        input=_build_user_prompt(
            query=query,
            doc_id=doc_id,
            case_year=case_year,
            matched_snippet=matched_snippet,
            full_document_text=full_document_text,
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "case_metadata",
                "schema": CASE_METADATA_JSON_SCHEMA,
                "strict": True,
            }
        },
    )
    raw = getattr(response, "output_text", "") or ""
    data = json.loads(raw)
    return CaseMetadata.model_validate(data)


def enrich_case_metadata(space: str, doc_id: str, query: str = "", matched_snippet: str | None = None) -> None:
    print(f"[case_metadata] Starting enrichment for {space}/{doc_id}", flush=True)
    try:
        row = get_metadata_row(space, doc_id)
    except MetadataStoreUnavailable:
        row = None
    attempts = int(row.get("attempt_count") or 0) if row else 0
    try:
        doc = search_engine.get_document_by_id(space, doc_id)
        if not doc or not doc.get("text"):
            raise RuntimeError("Document text not found.")

        text = doc["text"]
        extracted = extract_metadata_with_openai(
            query=query,
            doc_id=doc_id,
            case_year=doc.get("case_year"),
            matched_snippet=matched_snippet,
            full_document_text=text,
        )
        payload = {
            "space": space,
            "doc_id": doc_id,
            "status": "ready",
            "source_hash": source_hash(space, doc_id, text),
            "model": settings.CASE_METADATA_MODEL,
            "metadata": extracted.model_dump(),
            "error": None,
            "attempt_count": attempts + 1,
            "updated_at": _utcnow_iso(),
        }
    except (ValidationError, json.JSONDecodeError, Exception) as exc:
        payload = {
            "space": space,
            "doc_id": doc_id,
            "status": "failed",
            "model": settings.CASE_METADATA_MODEL,
            "error": str(exc),
            "attempt_count": attempts + 1,
            "updated_at": _utcnow_iso(),
        }
        print(f"[case_metadata] Enrichment failed for {space}/{doc_id}: {exc}", flush=True)

    saved = save_metadata_payload(payload)
    if saved and payload["status"] == "ready":
        print(f"[case_metadata] Finished enrichment for {space}/{doc_id}", flush=True)
