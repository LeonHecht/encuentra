from fastapi import APIRouter, Body, Depends, HTTPException
from backend.app.api.v1.schemas import ChatRequest, ChatResponse, Citation
from backend.app.services.bm25 import bm25_engine
from backend.app.dependencies import get_current_user
from openai import OpenAI
from backend.app.core.config import settings
import os

router = APIRouter()

# config
OPENAI_MODEL = settings.OPENAI_CHAT_MODEL
MAX_DOC_TOKENS = settings.MAX_DOC_TOKENS
MAX_DOCS = settings.MAX_DOCS

client = OpenAI()

SYSTEM_PROMPT = (
    "Eres un asistente jurídico. Responde SOLO usando el contexto provisto. "
    "Si el contexto no alcanza para responder con precisión, dilo. "
    "Incluye citas en el formato [doc_id]. Responde en español."
)

def approx_token_len(text: str) -> int:
    # quick heuristic: tokens ≈ 0.75 * words (good enough for budgeting)
    return int(len(text.split()) * 0.75)

def truncate_to_tokens(text: str, max_tokens: int) -> str:
    # inverse of the heuristic: words ≈ tokens / 0.75
    max_words = int(max_tokens / 0.75)
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])

@router.post("/chat", response_model=ChatResponse, summary="Ask the legal assistant (BM25-doc RAG)")
def chat(req: ChatRequest = Body(...), user=Depends(get_current_user)):
    # 1) retrieve top documents with BM25 (doc-level)
    hits = bm25_engine.search(req.question, top_k=max(5, MAX_DOCS), space=req.space)
    if not hits:
        return ChatResponse(answer="No encontré evidencia suficiente en el corpus.", citations=[])

    # 2) build context from the best N docs (trim each to MAX_DOC_TOKENS)
    context_blocks = []
    citations = []
    used_docs = 0

    for h in hits:
        doc_id = h["id"]
        doc = bm25_engine.get_document_by_id(req.space, doc_id)
        if not doc:
            continue
        full_text = doc.get("text", "") or ""
        if not full_text.strip():
            continue

        trimmed = truncate_to_tokens(full_text, MAX_DOC_TOKENS)
        title = (doc.get("title") or "").strip()

        # assemble a readable block; keep id for citations
        header = f"({doc_id}) {title}".strip() if title else f"({doc_id})"
        block = f"[{used_docs+1}] {header}\n{trimmed}"
        context_blocks.append(block)

        # citation object (use a short preview to avoid bloat)
        citations.append(Citation(doc_id=doc_id, snippet=trimmed[:240]))
        used_docs += 1
        if used_docs >= MAX_DOCS:
            break

    if not context_blocks:
        return ChatResponse(answer="No encontré evidencia suficiente en el corpus.", citations=[])

    context_text = "\n\n---\n\n".join(context_blocks)

    # 3) call OpenAI
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Pregunta: {req.question}\n\n"
                f"Contexto (máx {MAX_DOCS} documentos, {MAX_DOC_TOKENS} tokens c/u):\n{context_text}\n\n"
                "Instrucciones: Responde de manera concisa y cita con [doc_id]."
            ),
        },
    ]
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )
        answer = resp.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    return ChatResponse(answer=answer, citations=citations, file_url=None)
