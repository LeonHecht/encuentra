from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import json
from openai import OpenAI
from backend.app.core.config import settings
from backend.app.services.search import search_engine
from backend.app.dependencies import get_current_user

router = APIRouter()
client = OpenAI()

SYSTEM_PROMPT_V1 = """
Legal RAG Assistant — System Prompt (v2)

Role & audience
---------------
You are a precise, citation-driven legal assistant for El Salvador and LATAM case law.
Default to the user’s language. If the user writes in Spanish, answer in Spanish.

When to use tools
-----------------
Use tools when a claim depends on corpus content (cases, statutes, Diario Oficial, internal docs).
Answer directly (no tools) for general concepts/definitions or procedural how-tos that don’t require specific sources.

Planning loop (think → act → observe)
-------------------------------------
1. Brief internal plan.
2. If needed, call search_cases with a keyword-based query (for BM25 retriever).
3. Pick 5–10 promising doc IDs; call fetch_passages (2–3 passages per doc).
4. Summarize/answer with citations.
5. If the user asked for a list of many items (e.g., “robbery 2014”): iterate in small batches (3–5 items per turn), then ask if they want more.

Retrieval policy
----------------
- Start doc-level: search_cases(top_k=20); prefer precise queries over huge top_k.
- Then passage-level: fetch_passages(ids=5..10, per_id=2..3, max_tokens≈350).
- Avoid fetching full docs unless the user explicitly asks or the answer is impossible without it (like case summaries).
- If query is ambiguous, ask a short clarifying question before searching.

Token budgets (hard limits)
---------------------------
- Keep each tool result you pass into the model ≤ 4,096 tokens total.
- Typical: 8 docs × 2 passages × ~120–150 tokens each.
- Your final answer (without tool payloads) ≤ 350–500 tokens unless the user asks for a long brief.
- If the user requests summaries for many cases, do them in batches and cache earlier summaries.

Citations
---------
- After any factual claim based on retrieved text, add bracketed citations: [DocID §short-hint].
- Aggregate at paragraph ends when cleaner. Example:
  “El tribunal aclaró X… [10DB52 §Hechos].”
- Only cite docs you actually read via fetch_passages.

Answer formats
--------------
- If the user asks for a list/table/outline, return that structure (bullets or markdown table).
- For summaries of multiple cases, use a numbered list; each item: 
  Name/ID, Fecha, Hechos clave, Fallo, Relevancia, [citación].
- If the user uploads text and asks for analysis, include a short Limitations note if corpus support is thin.

Quality & safety
----------------
- Be concise, concrete, and neutral. 
- No legal advice disclaimers unless asked, but avoid definitive prescriptions (“debes”)—use informative tone.
- If results are thin or mixed, say so and suggest a refined search query.

Examples of routing
-------------------
- “¿Qué es hábeas corpus?” → Answer directly (no tools).
- “Resume 5 casos de robo de 2014” → search → pick IDs → fetch passages → summarize 3–5 now → ask to continue.
- “Dame jurisprudencia similar a X” → search with quoted key terms/entities → fetch → compare explicitly.

Tool defaults (unless user specifies)
-------------------------------------
search_cases.top_k = 5
fetch_passages.per_id = 2–3
fetch_passages.max_tokens ≈ 350
Batch large requests.
"""

TEST_SYS_PROMPT = """
You are a legal assistant. Answer in the language of the user.
"""


tools = [
  {
    "type": "function",
    "function": {
      "name": "search_cases",
      "description": "Lexical Keyword search (BM25) over indexed jurisprudence and laws.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": { "type": "string", "description": "User intent in plain Spanish in keywords." },
          "space": { "type": "string", "description": "Corpus scope (e.g., 'supreme_court' or user space)." },
          "filters": {
            "type": "object",
            "properties": {
              "year_from": { "type": "integer" },
              "year_to":   { "type": "integer" },
              "court":     { "type": "string" },
              "matter":    { "type": "string" }
            },
            "additionalProperties": False
          },
          "top_k": { "type": "integer", "default": 5, "minimum": 1, "maximum": 50 },
          "granularity": {
            "type": "string",
            "enum": ["doc", "chunk"],
            "default": "doc",
            "description": "Return doc-level hits, model can fetch passages later."
          }
        },
        "required": ["query"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "fetch_passages",
      "description": "Return top passages for selected hit IDs (de-duped, ordered).",
      "parameters": {
        "type": "object",
        "properties": {
          "ids": { "type": "array", "items": { "type": "string" }, "minItems": 1, "maxItems": 20 },
          "per_id": { "type": "integer", "default": 3, "minimum": 1, "maximum": 10 },
          "max_tokens": { "type": "integer", "default": 350, "minimum": 64, "maximum": 512 }
        },
        "required": ["ids"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "fetch_document",
      "description": "Return full text document (only if necessary, costly).",
      "parameters": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "max_tokens": { "type": "integer", "default": 2048, "minimum": 1024, "maximum": 4096 }
        },
        "required": ["id"]
      }
    }
  }
]

def sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\n" + f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

@router.get("/chat/stream")
# async def chat_stream(request: Request, response: Response, user=Depends(get_current_user)):
async def chat_stream(request: Request, response: Response):
    # print("Received /chat/stream request")

    token = request.query_params.get("token")
    # TODO: validate_token(token) -> raise HTTPException(401) if invalid

    # Parse inputs
    space = request.query_params.get("space") or ""
    # print(f"Using space: '{space}'")
    raw_messages = request.query_params.get("messages")
    if not raw_messages:
        raise HTTPException(status_code=400, detail="Missing messages")
    
    try:
        msgs: List[Dict[str, str]] = json.loads(raw_messages)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid messages JSON")
    
    # Build your RAG context (doc-level retrieval like before)
    hits = search_engine.search(msgs[-1]["content"], top_k=max(5, settings.MAX_DOCS), space=space)
    citations = []
    context_blocks = []
    used_docs = 0
    
    for h in hits or []:
        doc_id = h["id"]
        doc = search_engine.get_document_by_id(space, doc_id)
        if not doc:
            continue
        full_text = doc.get("text", "") or ""
        if not full_text.strip():
            continue

        trimmed = full_text[: settings.MAX_DOC_TOKENS * 4]
        title = (doc.get("title") or "").strip()
        header = f"({doc_id}) {title}".strip() if title else f"({doc_id})"
        block = f"[{used_docs+1}] {header}\n{trimmed}"
        context_blocks.append(block)

        citations.append({"doc_id": doc_id, "snippet": trimmed[:240]})
        used_docs += 1
        if used_docs >= settings.MAX_DOCS:
            break

    context_text = "\n\n---\n\n".join(context_blocks)
    # print(f"Built context with {used_docs} documents, {len(context_text)} characters")

    openai_messages = [
        {"role": "system", "content": TEST_SYS_PROMPT},
        {"role": "user", "content": f"Pregunta: {msgs[-1]['content']}\n\nContexto:\n{context_text}\n\nInstrucciones: Responde conciso y cita con [doc_id]."},
    ]

    def gen():
        try:
            stream = client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=openai_messages,
                stream=True,
            )
            parts = []
            for chunk in stream:
                delta = getattr(chunk.choices[0].delta, "content", None)
                if delta:
                    parts.append(delta)
                    yield sse("content", {"delta": delta})
            answer = "".join(parts)
            yield sse("done", {"answer": answer, "citations": citations, "file_url": None})
        except Exception as e:
            yield sse("content", {"delta": f"\n[error] {str(e)}"})
            yield sse("done", {"answer": "", "citations": [], "file_url": None})

    # Good SSE headers (FastAPI sets content-type; add no-cache/keep-alive)
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # If you use cookies across origins:
        # "Access-Control-Allow-Credentials": "true",
    }
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)
