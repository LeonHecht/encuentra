from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
from pydantic import BaseModel
from typing import Any
import re
import json
import textwrap
from openai import OpenAI
from backend.app.core.config import settings
from backend.app.services.search import search_engine
from backend.app.dependencies import get_current_user

from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional

@dataclass
class AgentConfig:
    model: str
    system_prompt: str
    tools: list
    max_iterations: int = 10
    parallel_tool_calls: bool = False
    reasoning_effort: str = "medium"
    reasoning_summary: str = "detailed"

@dataclass
class AgentContext:
    space: str
    openai_messages: List[Dict[str, Any]] = field(default_factory=list)
    last_user_msg: str = ""
    title: Optional[str] = None
    citations: List[Dict[str, str]] = field(default_factory=list)
    trace: List[Dict[str, Any]] = field(default_factory=list)
    iteration_count: int = 0
    final_answer: str = ""
    keep_reasoning: bool = True


class AgenticChatRequest(BaseModel):
    space: str
    messages: list[dict[str, Any]]   # role/content pairs
    state: str | None = None


router = APIRouter()
client = OpenAI()

FAST_SYS_PROMPT = """You are a helpful legal assistant for LATAM. Default to the user's language."""

SYSTEM_PROMPT_V1 = """
You are a precise, citation-driven legal assistant.
Default to the user’s language. If the user writes in Spanish, answer in Spanish.
Note: The Chat's logic is based on so called "Spaces" that the user can select. This space contains a collection of documents that will be searchable via the tools.
The Space can be public legal cases from El Salvador or the user's personal uploaded documents.
So when the user asks for information, that cannot be answered with public knowledge, assume the user wants you to search the selected Space.
When the user asks you to search in his/her documents, assume they refer to the selected Space.

## When to use tools
- Use tools for claims that depend on specific sources from the corpus (cases, statutes, Diario Oficial, internal documents).
- For general legal concepts, definitions, or procedural instructions that do not require a citation, answer directly without using tools.

## Planning loop
0. If the user's message can be answered directly without searching the corpus, skip the planning loop and answer directly. Else:
1. Rephrase the user's goal clearly, concisely, and in a friendly manner and emit a message informing the user via `emit_event`.
2. If necessary, decompose the user's query into sub-queries. For each sub-query:
- Brief internally on how to solve the sub-query.
- Emit a single function call to `emit_event` with an elaborated plan in a user-friendly language (2–6 bullet points).
- If corpus content is needed, call `search_cases` with a keyword-based query (for the BM25 retriever).
- Select 5–10 promising document IDs and call `fetch_passages` for 2–3 passages per document.
- Respond with bracketed citations after every factual claim based on retrieved text.
- If the user asks for a summary of a specific case, call `fetch_document` instead of `fetch_passages`.
- When you gathered all necessary information to provide the final answer back to the user. Do not include the user intent in your response, just respond naturally as if it was a normal conversation.
- If at any point you need clarification or a selection from the user, respond with a clear prompt, so after getting back the clarification from the user, you can proceed with the reasoning. But try to assume the most likely intent of the user and avoid asking for clarifications unless absolutely necessary.

## Citations
- Include bracketed citations: [DocID §citation] after any factual assertion based on a specific document. The citation you include can be 1-3 sentences or shorter, depending on the situation.
- If multiple documents support the same claim, GROUP them in a single bracket like: [38949; 38950] or [38949 §nota; 38950]. Do not emit adjacent brackets like [38949] [38950].
- Cite only documents actually reviewed through `fetch_passages` or `fetch_document`.

## Output Format
- ALWAYS PROVIDE YOUR ANSWER IN MARKDOWN!

## Quality & Safety
- Be concise, concrete, and neutral. 
- Do not provide legal advice disclaimers unless explicitly requested.
- Avoid definitive prescriptions (“debes”); maintain an informative tone.
- If sourced information is insufficient or ambiguous, state this clearly and suggest a refined search.
- Remember, you only have access to the local database containing legal documents from El Salvador and Paraguay, don't propose to the user to search any external databases or the internet (not possible).

## Examples of Query Routing
- “¿Qué es hábeas corpus?” → Answer directly (no tools).
- “Resume 5 casos de robo de 2014” → Search → select IDs → fetch passages → summarize 3–5 cases → ask if the user wishes to continue.
- “Dame jurisprudencia similar a X” → Search using quoted terms/entities → fetch → compare and summarize findings.
"""

# TEST_SYS_PROMPT = """
# You are a legal assistant. Answer in the language of the user.
# Operational rule: First, emit a single function call to `report_trace` with a brief plan (2–6 bullets),
# then proceed to call tools as needed. Keep the plan concise and non-sensitive.
# """

emit_msg_tool = {
  "type": "function",
  "name": "emit_event",
  "description": "Emit a short, user-visible reasoning note (user's goal, plan, decision, progress).",
  "parameters": {
    "type": "object",
    "properties": {
      "kind": { "type": "string", "enum": ["user_goal_plan","decision","note","progress"] },
      "message": { "type": "string" },
    },
    "required": ["message"]
  }
}

# finalizer_tool = {
#   "type": "function",
#   "name": "submit_answer",
#   "description": "Call this exactly once when you are completely done or need clarification from the user. It returns a response message to the user.",
#   "parameters": {
#     "type": "object",
#     "properties": {
#       "answer": { "type": "string", "description": "Response to user." },
#       "citations": {
#         "type": "array",
#         "items": { "type": "object", "properties": {
#           "doc_id": { "type": "string" },
#           "snippet": { "type": "string" }
#         } },
#         "description": "Optional citations used in the answer."
#       }
#     },
#     "required": ["answer"]
#   }
# }

# report_trace_tool = {
#     "type": "function",
#     "name": "report_trace",
#     "description": "Provide a brief, non-sensitive plan and the tools you intend to call next.",
#     "parameters": {
#         "type": "object",
#         "properties": {
#         "plan": {
#             "type": "array",
#             "items": { "type": "string" },
#             "description": "2–6 concise bullets describing the approach. Give a short reason for each step.",
#             "minItems": 1,
#             "maxItems": 6
#         },
#         "intended_tools": {
#             "type": "array",
#             "items": { "type": "string", "enum": ["search_cases", "fetch_passages", "fetch_document"] },
#             "description": "Which tools you’ll likely use, in rough order.",
#             "minItems": 0,
#             "maxItems": 5
#         },
#         "stop_condition": {
#             "type": "string",
#             "description": "When you’ll stop calling tools."
#         }
#         },
#         "required": ["plan"]
#     }
# }

tools = [
    emit_msg_tool,
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
        "description": "Return full text document (costly; avoid unless needed (e.g. case summaries)).",
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

def sanitize_output_items(raw_items):
    """Convert SDK output items to API-acceptable input items."""
    sanitized = []
    for it in raw_items or []:
        obj = it.model_dump() if hasattr(it, "model_dump") else it
        t = obj.get("type")

        if t == "function_call":
            sanitized.append({
                "type": "function_call",
                "name": obj.get("name"),
                # must be a JSON STRING, not dict
                "arguments": obj.get("arguments") or "{}",
                "call_id": obj.get("call_id"),
            })
        elif t == "function_call_output":
            sanitized.append({
                "type": "function_call_output",
                "call_id": obj.get("call_id"),
                "output": obj.get("output", ""),
            })
        elif t == "message":
            # keep only role+content (optional; you can drop messages entirely)
            role = obj.get("role")
            parts = obj.get("content") or []
            text = ""
            if isinstance(parts, list):
                text = "".join(p.get("text","") for p in parts if isinstance(p, dict))
            elif isinstance(parts, str):
                text = parts
            if role in ("user","assistant","system"):
                sanitized.append({"role": role, "content": text})
        else:
            # drop 'reasoning' and anything else
            continue
    return sanitized

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
        result_info = str(result)
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


# DEPRECATED: use /chat/agentic instead
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
        {"role": "system", "content": "Your are a legal assistant for El Salvador. Answer concisely and cite with [doc_id]."},
        {"role": "user", "content": f"Pregunta: {msgs[-1]['content']}\n\nContexto:\n{context_text}\n\nInstrucciones: Responde conciso y cita con [doc_id]."},
    ]

    def gen():
        try:
            stream = client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=openai_messages,
                stream=True
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


def normalize_title(raw: str | None, fallback: str | None) -> str | None:
    """Trim quotes/whitespace and cap to 5 words. Fallback to first 5 words of user msg if empty."""
    t = (raw or "").strip().strip('"').strip("'")
    t = re.sub(r"\s+", " ", t)
    if not t and fallback:
        t = " ".join((fallback or "").split()[:5]).strip()
    if t:
        t = " ".join(t.split()[:5])
        return t or None
    return None

def extract_inline_citations(text: str):
    # Parse inline [DocID §citation] markers from the final answer so the UI can place citations exactly inline.
    # Matches [DocID] or [DocID §hint]; DocID excludes closing bracket and whitespace
    # Examples: [38949], [38949 §sentencia condenatoria]
    pattern = re.compile(r"\[([^\]\s]+)(?:\s*§\s*([^\]]+))?\]")
    occ = []
    for m in pattern.finditer(text or ""):
        doc_id = (m.group(1) or "").strip()
        cite = (m.group(2) or "").strip() if m.lastindex and m.group(2) else ""
        occ.append({
            "doc_id": doc_id,
            "cite": cite,
            "start": m.start(),
            "end": m.end(),
        })
    return occ

def get_title_for_chat(last_user_msg):
    try:
        # print("\n📝 **Generating Chat Title**")
        response = client.responses.create(
            model="gpt-4.1-nano",
            instructions="Given this user's request, give the Chat a title that will be shown in the list of chats. Return a string of max 5 words. Don't return any additional content, just the title.",
            input=[{"role": "user", "content": last_user_msg[:200]}],
            # reasoning={"effort": "low"},
        )
        raw_title = response.output_text
        title = normalize_title(raw_title, last_user_msg)
        # print(f"Generated title: {title}")
    except Exception as e:
        print(f"[title] generation failed: {e}")
        title = normalize_title("", last_user_msg)
    return title

def is_respond_fast(last_user_msg):
    try:
        # print("\n📝 **Deciding if to respond fast**")
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions="Determine whether the following user’s request can be answered directly from internal knowledge. If yes, respond 'yes'. If it requires complex reasoning or external case law lookup, respond 'no'.",
            input=[{"role": "user", "content": f"User request:\n{last_user_msg}\nIf the request can be answered without searching case law or reasoning, return 'yes', else 'no'."}],
            # reasoning={"effort": "low"},
        )
        # print("response:", response.output_text)
        if "yes" in response.output_text.strip().lower():
            # print("Decided to respond fast.")
            return True
        elif "no" in response.output_text:
            # print("Decided to use full reasoning.")
            return False
        else:
            # print("Could not decide; defaulting to full reasoning.")
            return False
    except Exception as e:
        print(f"[title] generation failed: {e}")
        
def run_tool(ctx: AgentContext, tool_name, tool_args) -> str:
    """ do before: tool_args = json.loads(item.arguments) """
    
    def push_trace(evt):  # uniform schema for UI
        # evt: {type, step, tool?, args?, message?, status?, result_count?}
        ctx.trace.append(evt)
    
    if tool_name == "emit_event":
        # result to be ack'd back into openai_messages later
        result = json.dumps({"ok": True})
        
        push_trace({
            "type": "reasoning",
            "step": ctx.iteration_count,
            "message": tool_args.get("message",""),
            "kind": tool_args.get("kind","note"),
        })

        log_tool_call(ctx.iteration_count, tool_name, tool_args, "emitted")
    
    elif tool_name == "search_cases":
        query = tool_args.get("query", ctx.last_user_msg)
        filters = tool_args.get("filters", {})
        top_k = int(tool_args.get("top_k", 5))

        push_trace({"type":"tool_start","step":ctx.iteration_count,"tool":"search_cases","args":{"query": query,"filters":filters,"top_k":top_k}})
        result = search_cases(query=query, space=ctx.space, filters=filters, top_k=top_k)
        push_trace({"type":"tool_result","step":ctx.iteration_count,"tool":"search_cases","result_count":len(result)})
        log_tool_call(ctx.iteration_count, tool_name, tool_args, result)

    elif tool_name == "fetch_passages":
        ids = tool_args.get("ids", [])
        per_id = int(tool_args.get('per_id', 3))
        max_tokens = int(tool_args.get('max_tokens', 350))

        push_trace({"type":"tool_start","step":ctx.iteration_count,"tool":"fetch_passages","args":{"ids":ids,"per_id":per_id,"max_tokens":max_tokens}})
        result = fetch_passages(query=ctx.last_user_msg, ids=ids, space=ctx.space, per_id=per_id, max_tokens=max_tokens)
        try:
            for p in result or []:
                did = (p or {}).get("doc_id") or (p or {}).get("id")
                if did:
                    snip = (p or {}).get("passage") or (p or {}).get("snippet") or ""
                    ctx.citations.append({"doc_id": did, "snippet": snip[:400]})
        except Exception as _e:
            pass
        push_trace({"type":"tool_result","step":ctx.iteration_count,"tool":"fetch_passages","result_count":len(result)})
        log_tool_call(ctx.iteration_count, tool_name, tool_args, result)
    
    elif tool_name == "fetch_document":                    
        doc_id = tool_args.get("id", "")
        max_tokens = int(tool_args.get("max_tokens", 2048))

        push_trace({"type":"tool_start","step":ctx.iteration_count,"tool":"fetch_document","args":{"id":doc_id,"max_tokens":max_tokens}})
        result = fetch_document(id=doc_id, space=ctx.space, max_tokens=max_tokens)
        try:
            if isinstance(result, dict):
                did = result.get("id") or doc_id
                txt = (result.get("text") or "")
                if did and txt:
                    ctx.citations.append({"doc_id": did, "snippet": txt[:240]})
        except Exception as _e:
            pass
        push_trace({"type":"tool_result","step":ctx.iteration_count,"tool":"fetch_document","result_count":1 if result else 0})
        log_tool_call(ctx.iteration_count, tool_name, tool_args, result)            
    
    else:
        print(f"❌ **Unknown tool name: {tool_name}**")
        result = "Unknown tool"

    return result

def dedupe_citations(cites: list[dict]) -> list[dict]:
    seen = set(); out=[]
    for c in cites:
        did = c.get("doc_id")
        if did and did not in seen:
            out.append(c); seen.add(did)
    return out

import asyncio
import json

@router.post("/chat/agentic/stream")
async def chat_agentic_stream(req: AgenticChatRequest):
    
    openai_messages: list[dict[str, Any]] = []
    if req.state:
        try:
            s = json.loads(req.state)
            if isinstance(s, list):
                openai_messages = s
        except Exception as e:
            print("bad state:", e)

    last_user_msg = req.messages[-1]['content']
    openai_messages.append({"role": "user", "content": last_user_msg})
    # print(f"openai_messages: {openai_messages}")

    ctx = AgentContext(space=req.space, openai_messages=openai_messages, last_user_msg=last_user_msg)
    cfg = AgentConfig(model=settings.OPENAI_CHAT_MODEL, system_prompt=SYSTEM_PROMPT_V1, tools=tools)

    # final_answer = ""
    # citations: list[dict[str, str]] = []
    # keep_reasoning = True
    # max_iterations = 10
    # iteration_count = 0
    # trace: list[dict[str, Any]] = []

    # title: str | None = None
    if len(openai_messages) == 1:
        set_title = True
    else:
        set_title = False

    async def event_stream():
        nonlocal ctx, cfg

        # helper to emit SSE json with a custom event name
        async def emit(event: str, obj: dict):
            yield f"event: {event}\n".encode("utf-8")
            yield f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode("utf-8")

        if is_respond_fast(last_user_msg):
            stream = client.responses.create(
                model="gpt-4.1-mini",
                instructions=FAST_SYS_PROMPT,
                input=ctx.openai_messages,
                stream=True,
            )

            # Local accumulator for this streamed turn
            acc_text: list[str] = []

            for ev in stream:
                t = getattr(ev, "type", None)

                # Output text
                if t == "response.output_text.delta":
                    d = getattr(ev, "delta", "") or ""
                    acc_text.append(d)
                    await asyncio.sleep(0)  # optional, helps flush
                    async for chunk in emit("response.output_text.delta", {"step": ctx.iteration_count, "delta": d}):
                        yield chunk
                if t == "response.output_text.done":
                    txt = getattr(ev, "text", "") or ""
                    ctx.final_answer = txt or "".join(acc_text)
                    await asyncio.sleep(0)  # optional, helps flush
                    async for chunk in emit("response.output_text.done", {"step": ctx.iteration_count, "text": ctx.final_answer}):
                        yield chunk

                    if ctx.final_answer:
                        ctx.openai_messages.append({
                            "role": "assistant",
                            "content": ctx.final_answer
                        })
                    ctx.keep_reasoning = False

                # Completion
                if t == "response.completed":
                    pass

            stream.close()

        while ctx.keep_reasoning and ctx.iteration_count < cfg.max_iterations:
            ctx.iteration_count += 1
            # print(f"\n🔄 **Reasoning Iteration {ctx.iteration_count}**")

            if ctx.iteration_count == cfg.max_iterations:
                extra_finalize_note = (
                    "You have reached the maximum reasoning iterations. "
                    "Do NOT call more tools. Produce the final answer now. If you still couldn't gather enough information, state that clearly in your answer. It is better to be honest than to invent information."
                )
                final_instructions = f"{cfg.system_prompt}\n\n[control] {extra_finalize_note}"
            else:
                final_instructions = cfg.system_prompt

            stream = client.responses.create(
                model=cfg.model,
                instructions=final_instructions,
                input=ctx.openai_messages,
                tools=cfg.tools,
                parallel_tool_calls=cfg.parallel_tool_calls,
                reasoning={"effort": cfg.reasoning_effort, "summary": cfg.reasoning_summary},
                max_tool_calls=cfg.max_iterations,
                tool_choice="auto",
                stream=True,
            )

            # Local accumulators for this streamed turn
            acc_text: list[str] = []
            
            final_tool_calls = {}
            for ev in stream:
                t = getattr(ev, "type", None)

                # Output Item
                if t == "response.output_item.added":
                    if ev.item.type == "function_call":
                        final_tool_calls[ev.output_index] = ev.item
                    elif ev.item.type == "reasoning":
                        pass  # no action needed

                # Reasoning (UI)
                if t == "response.reasoning_summary_text.delta":
                    pass
                if t == "response.reasoning_text.delta":
                    pass
                if t == "response.reasoning_summary_part.added":
                    pass

                # Function tools
                if t == "response.function_call_arguments.delta":
                    index = ev.output_index
                    if final_tool_calls[index]:
                        final_tool_calls[index].arguments += ev.delta

                if t == "response.function_call_arguments.done":
                    index = ev.output_index
                    tool_call = final_tool_calls[index]
                    tool_name = getattr(tool_call, "name")
                    tool_args = json.loads(getattr(tool_call, "arguments"))

                    if tool_name == "emit_event":
                        msg = tool_args.get("message", "Pensando")
                    elif tool_name == "search_cases":
                        query = tool_args.get("query", "[Consulta no disponible.]")
                        msg = f"Buscando documentos relevantes a la siguiente consulta: {query}..."
                    elif tool_name == "fetch_passages":
                        msg = "Recuperando pasajes relevantes..."
                    elif tool_name == "fetch_document":
                        msg = "Recuperando documentos relevantes..."
                    else:
                        break
                    
                    await asyncio.sleep(0)  # optional, helps flush
                    async for chunk in emit("response.emit_message", {"step": ctx.iteration_count, "msg": msg}):
                        yield chunk
                    
                    break
                
                # Output text
                if t == "response.output_text.delta":
                    d = getattr(ev, "delta", "") or ""
                    acc_text.append(d)
                    await asyncio.sleep(0)  # optional, helps flush
                    async for chunk in emit("response.output_text.delta", {"step": ctx.iteration_count, "delta": d}):
                        yield chunk
                if t == "response.output_text.done":
                    txt = getattr(ev, "text", "") or ""
                    ctx.final_answer = txt or "".join(acc_text)
                    await asyncio.sleep(0)  # optional, helps flush
                    async for chunk in emit("response.output_text.done", {"step": ctx.iteration_count, "text": ctx.final_answer}):
                        yield chunk

                    if ctx.final_answer:
                        ctx.openai_messages.append({
                            "role": "assistant",
                            "content": ctx.final_answer
                        })
                    ctx.keep_reasoning = False

                # Completion
                if t == "response.completed":
                    pass

            stream.close()

            for tool_call_index in final_tool_calls:
                tool_call = final_tool_calls[tool_call_index]
                    
                tool_name = getattr(tool_call, "name")
                tool_args = json.loads(getattr(tool_call, "arguments"))
                call_id = getattr(tool_call, "call_id")

                ctx.openai_messages.append({
                    "type": "function_call",
                    "name": tool_name,
                    "arguments": json.dumps(tool_args, ensure_ascii=False),
                    "call_id": call_id
                })

                result = run_tool(ctx, tool_name, tool_args)

                # clip result to prevent context balooning (cost management)
                result = clip(str(result))

                print(f"🛠️ **Tool {tool_name} returned result (start): {result}**")

                # Append tool call and observation to messages for next iteration
                ctx.openai_messages.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": str(result),
                })
            
            continue  # next reasoning iteration

        if ctx.final_answer == "":
            ctx.final_answer = (
                "No pude completar el razonamiento completo para contestar su pregunta. "
                "¿Te parece bien que resuma los resultados encontrados hasta ahora?"
            )

        inline_occurrences = extract_inline_citations(ctx.final_answer)

        if set_title and not ctx.title:
            ctx.title = get_title_for_chat(last_user_msg)

        completed_payload = {
            "answer": ctx.final_answer,
            "title": ctx.title,
            "citations": dedupe_citations(ctx.citations),
            "inline_citations": inline_occurrences,
            "trace_len": len(ctx.openai_messages),
            "trace": ctx.trace,
            "agent_state": json.dumps(ctx.openai_messages),
        }

        # Final summary event (mirrors your non-stream return payload)
        async for chunk in emit("response.completed", completed_payload):
            yield chunk
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
