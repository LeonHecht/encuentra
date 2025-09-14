from __future__ import annotations

import uuid
from typing import Dict

# simple in-memory token store mapping token -> username
tokens_db: Dict[str, str] = {}


def create_access_token(data: dict) -> str:
    """Return a new access token for the given payload.

    The token is a random uuid mapped to the username (``sub``) in
    an in-memory store so that the tests can inspect and the API can
    validate it without external dependencies.
    """
    token = uuid.uuid4().hex
    username = data.get("sub")
    tokens_db[token] = username
    return token


def verify_access_token(token: str) -> dict:
    """Validate *token* and return a payload containing ``sub``."""
    username = tokens_db.get(token)
    if not username:
        raise ValueError("Invalid token")
    return {"sub": username}
