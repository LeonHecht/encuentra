from fastapi import Header, HTTPException
from fastapi.security import HTTPBearer

from app.services.auth import users_db, UserData
from app.core.security import verify_access_token

def get_current_user(authorization: str = Header(None)) -> UserData:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, detail="Invalid or missing Authorization header")
    token = authorization.split()[1]          # strip “Bearer ”
    try:
        payload = verify_access_token(token)
        username = payload.get("sub")
    except ValueError:
        raise HTTPException(401, detail="Invalid token")
    user = users_db.get(username)
    if not user:
        raise HTTPException(401, detail="User not found")
    return user
