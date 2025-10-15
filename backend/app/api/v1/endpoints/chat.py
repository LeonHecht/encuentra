from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import json
import textwrap
from openai import OpenAI
from backend.app.core.config import settings
from backend.app.services.search import search_engine
from backend.app.dependencies import get_current_user

router = APIRouter()
client = OpenAI()

SYSTEM_PROMPT_V1 = """
Legal RAG Assistant — System Prompt

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
Operational rule: First, emit a single function call to `report_trace` with a brief plan (2–6 bullets),
then proceed to call tools as needed. Keep the plan concise and non-sensitive.
"""

tools = [
    {
        "type": "function",
        "name": "report_trace",
        "description": "Provide a brief, non-sensitive plan and the tools you intend to call next.",
        "parameters": {
            "type": "object",
            "properties": {
            "plan": {
                "type": "array",
                "items": { "type": "string" },
                "description": "2–6 concise bullets describing the approach. Give a short reason for each step.",
                "minItems": 1,
                "maxItems": 6
            },
            "intended_tools": {
                "type": "array",
                "items": { "type": "string", "enum": ["search_cases", "fetch_passages", "fetch_document"] },
                "description": "Which tools you’ll likely use, in rough order.",
                "minItems": 0,
                "maxItems": 5
            },
            "stop_condition": {
                "type": "string",
                "description": "When you’ll stop calling tools."
            }
            },
            "required": ["plan"]
        }
    },
    {
        "type": "function",
        "name": "search_cases",
        "description": "Lexical Keyword search (BM25) over indexed jurisprudence and laws.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "User intent in plain Spanish in keywords."},
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
            },
            "required": ["query"]
        }
    },
    {
        "type": "function",
        "name": "fetch_passages",
        "description": "Return top passages for selected doc IDs (ordered).",
        "parameters": {
        "type":"object",
        "properties":{
            "ids":{"type":"array","items":{"type":"string"},"minItems":1,"maxItems":20},
            "per_id":{"type":"integer","default":3,"minimum":1,"maximum":10},
            "max_tokens":{"type":"integer","default":350,"minimum":64,"maximum":512},
        },
        "required":["ids"]
        }
    },
    {
        "type": "function",
        "name": "fetch_document",
        "description": "Return full text document (costly; avoid unless needed).",
        "parameters": {
            "type":"object",
            "properties":{
            "id":{"type":"string"},
            "max_tokens":{"type":"integer","default":2048,"minimum":512,"maximum":4096}
            },
            "required":["id"]
        }
    }
]

def log_tool_call(step: int, name: str, args: dict, result: Any):
    # keep logs readable & bounded
    args_preview = json.dumps(args, ensure_ascii=False)[:1000]
    if isinstance(result, (dict, list)):
        # count-y summary to avoid dumping full payloads
        if isinstance(result, list):
            result_info = f"list(len={len(result)})"
        else:
            result_info = f"dict(keys={list(result.keys())[:6]})"
    else:
        result_info = str(result)[:300]
    print(textwrap.dedent(f"""
    🧰 Tool Step {step}
    ├─ name: {name}
    ├─ args: {args_preview}
    └─ result: {result_info}
    """).rstrip())

def search_cases(query: str, space: str = "", filters: Dict[str, Any] = {}, top_k: int = 5) -> List[Dict[str, Any]]:
    """ query OpenSearch and return compact hits (IDs + short snippets + meta)
    """
    # perform search; Filters will be implemented lateron (TODO)
    hits = search_engine.search(query=query, top_k=top_k, space=space)

    # hits has [{"id", "title", "score", "snippet", "download_url"}]
    return hits

def fetch_passages(query: str, ids: List[str], space: str = "", per_id: int = 3, max_tokens: int = 350) -> List[Dict[str, Any]]:
    """Return top passages for selected hit IDs (ordered). """
    passages = []

    for id in ids:
        top_passages_for_id = search_engine.fetch_passages(space=space,
                                                            doc_id=id,
                                                            query=query,
                                                            per_id=per_id,
                                                            max_tokens=max_tokens)
        passages.extend(top_passages_for_id)
    
    return passages

def fetch_document(id: str, space: str = "", max_tokens: int = 2048) -> Dict[str, Any]:
    doc = search_engine.get_document_by_id(space=space, doc_id=id)
    if doc is None:
        print("[fetch_document] Document not found:", id)
    elif doc.get("text") == "":
        print("[fetch_document] Document has empty text:", id)
    return doc if doc is not None else {}

def clip(s, max_chars=16000):
    return s if len(s)<=max_chars else s[:max_chars]

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


@router.get("/chat/agentic")
# async def chat_stream(request: Request, response: Response, user=Depends(get_current_user)):
async def chat_agentic(request: Request, response: Response):
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
    
    last_user_msg = msgs[-1]['content']

    openai_messages = [
        {"role": "user", "content": last_user_msg}
    ]

    final_answer = ""
    citations = []

    keep_reasoning = True
    max_iterations = 6
    iteration_count = 0

    while keep_reasoning and iteration_count < max_iterations:
        iteration_count += 1
        print(f"\n🔄 **Reasoning Iteration {iteration_count}**")

        response = client.responses.create(
            model=settings.OPENAI_CHAT_MODEL,
            instructions=TEST_SYS_PROMPT,
            input=openai_messages,
            tools=tools,
            parallel_tool_calls=False,
        )

        print("\n✨ **Initial Response Output:**")
        print(response.output)

        openai_messages += response.output

        for item in response.output:
            print(f"Response type: {item.type}")
            if item.type == "reasoning":
                print("🧠 **Model took reasoning step**")
                # Continue the loop to let the model decide next action
                continue
            if item.type == "function_call":
                tool_name = item.name      # ["search_cases", "fetch_passages", "fetch_document"]
                print(f"\n🔧 **Model triggered a tool call:** {tool_name}")

                if tool_name == "report_trace":
                    try:
                        plan = json.loads(item.arguments or "{}")
                    except Exception:
                        plan = {}
                    print("\n🧭 Plan from model:")
                    for i, s in enumerate(plan.get("plan", []), 1):
                        print(f"  {i}. {s}")
                    print(f"   intended_tools: {plan.get('intended_tools', [])}")
                    if plan.get("stop_condition"):
                        print(f"   stop_condition: {plan['stop_condition']}")
                    # Ack back so the model knows we recorded it
                    openai_messages.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps({"ok": True})
                    })
                    # don't set keep_reasoning=False; this is just a preface
                    continue
                elif tool_name == "search_cases":
                    tool_args = json.loads(item.arguments)
                    query = tool_args.get("query", last_user_msg)
                    filters = tool_args.get("filters", {})
                    top_k = int(tool_args.get("top_k", 5))
                    print(f"Calling search_cases with query='{query}', filters={filters}, top_k={top_k}")
                    result = search_cases(query=query, space=space, filters=filters, top_k=top_k)
                    log_tool_call(iteration_count, tool_name, tool_args, result)

                elif tool_name == "fetch_passages":
                    tool_args = json.loads(item.arguments)
                    ids = tool_args.get("ids", [])
                    per_id = int(tool_args.get('per_id', 3))
                    max_tokens = int(tool_args.get('max_tokens', 350))
                    print(f"Calling fetch_passages with ids={ids}, per_id={per_id}, max_tokens={max_tokens}")
                    result = fetch_passages(query=last_user_msg, ids=ids, space=space, per_id=per_id, max_tokens=max_tokens)
                    log_tool_call(iteration_count, tool_name, tool_args, result)
                
                elif tool_name == "fetch_document":                    
                    tool_args = json.loads(item.arguments)
                    doc_id = tool_args.get("id", "")
                    max_tokens = int(tool_args.get("max_tokens", 2048))
                    print(f"Calling fetch_document with id={doc_id}, max_tokens={max_tokens}")
                    result = fetch_document(id=doc_id, space=space, max_tokens=max_tokens)
                    log_tool_call(iteration_count, tool_name, tool_args, result)

                else:
                    print(f"❌ **Unknown tool name: {tool_name}**")
                    result = "Unknown tool"

                # clip result to prevent context balooning (cost management)
                result = clip(str(result))

                # Append tool call and observation to messages for next iteration
                openai_messages.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": str(result),
                })
            elif item.type == "message":
                # If no tool call is triggered, print the response directly.
                print("💡 **Final Answer:**")
                final_answer = response.output_text
                print(final_answer)
                keep_reasoning = False
            else:
                print(f"❓ **Unknown response type: {item.type}**")
    # # Good SSE headers (FastAPI sets content-type; add no-cache/keep-alive)
    # headers = {
    #     "Cache-Control": "no-cache",
    #     "Connection": "keep-alive",
    #     # If you use cookies across origins:
    #     # "Access-Control-Allow-Credentials": "true",
    # }
    return {
        "answer": final_answer,
        "citations": dedupe_citations(citations),
        "tool_steps": iteration_count,
        "trace_len": len(openai_messages),
    }

def dedupe_citations(cites: list[dict]) -> list[dict]:
    seen = set(); out=[]
    for c in cites:
        did = c.get("doc_id")
        if did and did not in seen:
            out.append(c); seen.add(did)
    return out