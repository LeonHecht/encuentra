from fastapi import Header, HTTPException
from app.services.auth import tokens_db, users_db, UserData


def get_current_user(authorization: str = Header(None)) -> UserData:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, detail="Invalid or missing Authorization header")
    token = authorization[7:]
    username = tokens_db.get(token)
    if not username:
        raise HTTPException(401, detail="Invalid token")
    user = users_db.get(username)
    if not user:
        raise HTTPException(401, detail="User not found")
    return user
