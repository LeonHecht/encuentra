from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.schemas import LoginRequest, LoginResponse, SpaceCreateRequest
from app.dependencies import get_current_user
from app.services.auth import authenticate, create_user_space, get_accessible_spaces, UserData
from app.services.bm25 import bm25_engine

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    token = authenticate(req.username, req.password)
    if not token:
        raise HTTPException(401, detail="Invalid credentials")
    return LoginResponse(token=token)

@router.get("/user/spaces")
def list_user_spaces(user: UserData = Depends(get_current_user)):
    return {"spaces": get_accessible_spaces(user.username)}

@router.post("/user/spaces")
def create_space(req: SpaceCreateRequest, user: UserData = Depends(get_current_user)):
    try:
        space_key = create_user_space(user.username, req.name)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    bm25_engine.index(space_key)
    return {"space": space_key}
