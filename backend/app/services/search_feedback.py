from __future__ import annotations

from typing import Any

from backend.app.services.auth import UserData, get_supabase_for_user


def log_search_query(
    *,
    user: UserData,
    query_text: str,
    space: str,
    top_k: int,
    year_filter: int | None,
    result_count: int,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    """Persist a search session and return its UUID.

    Search should remain available if logging is temporarily unavailable, so
    callers are expected to tolerate a None return value.
    """
    payload = {
        "user_id": user.user_id,
        "query_text": query_text,
        "space": space,
        "top_k": top_k,
        "year_filter": year_filter,
        "result_count": result_count,
        "metadata": metadata or {},
    }
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
