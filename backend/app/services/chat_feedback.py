from __future__ import annotations

from typing import Any

from backend.app.services.auth import UserData, get_supabase_for_user


def save_chat_message_feedback(
    *,
    user: UserData,
    chat_id: str,
    assistant_message_id: str,
    space: str | None,
    previous_user_message: str | None,
    previous_messages: list[dict[str, Any]],
    assistant_response: str,
    citations: list[dict[str, Any]],
    feedback: str,
    feedback_text: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    payload = {
        "user_id": user.user_id,
        "chat_id": chat_id,
        "assistant_message_id": assistant_message_id,
        "space": space,
        "previous_user_message": previous_user_message,
        "previous_messages": previous_messages,
        "assistant_response": assistant_response,
        "citations": citations,
        "feedback": feedback,
        "feedback_text": feedback_text,
        "metadata": metadata or {},
    }

    sb = get_supabase_for_user(user)
    existing = (
        sb.table("chat_message_feedback")
        .select("id")
        .eq("user_id", user.user_id)
        .eq("assistant_message_id", assistant_message_id)
        .execute()
    )

    if existing.data:
        row_id = existing.data[0]["id"]
        resp = (
            sb.table("chat_message_feedback")
            .update(payload)
            .eq("id", row_id)
            .execute()
        )
    else:
        resp = sb.table("chat_message_feedback").insert(payload).execute()

    return resp.data[0] if resp.data else None
