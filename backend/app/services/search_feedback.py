from __future__ import annotations

from functools import lru_cache
from typing import Any

from postgrest.types import ReturnMethod
from supabase import Client, ClientOptions, create_client

from backend.app.core.config import settings
from backend.app.services.auth import UserData, get_supabase_for_user


@lru_cache(maxsize=1)
def _get_anonymous_search_log_client() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise RuntimeError("Supabase backend credentials are required for anonymous search logs.")
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
        options=ClientOptions(postgrest_client_timeout=2, auto_refresh_token=False, persist_session=False),
    )


def log_search_query(
    *,
    user: UserData | None,
    query_text: str,
    space: str,
    top_k: int,
    year_filter: int | None,
    result_count: int,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Persist a website or anonymous MCP search and return its UUID when available.

    Search should remain available if logging is temporarily unavailable, so
    callers are expected to tolerate a None return value.
    """
    payload = {
        "user_id": user.user_id if user is not None else None,
        "query_text": query_text,
        "space": space,
        "top_k": top_k,
        "year_filter": year_filter,
        "result_count": result_count,
        "metadata": metadata or {},
    }
    if user is None:
        _get_anonymous_search_log_client().table("search_query_logs").insert(
            payload, returning=ReturnMethod.minimal,
        ).execute()
        return None

    resp = get_supabase_for_user(user).table("search_query_logs").insert(payload).execute()
    if not resp.data:
        return None
    return resp.data[0].get("id")


def save_search_result_feedback(
    *,
    user: UserData,
    query_log_id: str | None,
    query_text: str,
    space: str,
    top_k: int | None,
    year_filter: int | None,
    doc_id: str,
    rank: int,
    score: float | None,
    title: str | None,
    snippet: str | None,
    feedback: str,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    payload = {
        "user_id": user.user_id,
        "query_log_id": query_log_id,
        "query_text": query_text,
        "space": space,
        "top_k": top_k,
        "year_filter": year_filter,
        "doc_id": doc_id,
        "rank": rank,
        "score": score,
        "title": title,
        "snippet": snippet,
        "feedback": feedback,
        "reason": reason,
        "metadata": metadata or {},
    }

    sb = get_supabase_for_user(user)
    existing = (
        sb.table("search_result_feedback")
        .select("id")
        .eq("user_id", user.user_id)
        .eq("query_text", query_text)
        .eq("space", space)
        .eq("doc_id", doc_id)
        .execute()
    )

    if existing.data:
        row_id = existing.data[0]["id"]
        resp = (
            sb.table("search_result_feedback")
            .update(payload)
            .eq("id", row_id)
            .execute()
        )
    else:
        resp = sb.table("search_result_feedback").insert(payload).execute()

    return resp.data[0] if resp.data else None
