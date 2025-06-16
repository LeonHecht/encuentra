from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.schemas import (
    LoginRequest,
    LoginResponse,
    SpaceCreateRequest,
    RegisterRequest,
    UserInfo,
)
from app.dependencies import get_current_user
from app.services.auth import (
    authenticate,
    create_user_space,
    get_accessible_spaces,
    register_user,
    user_exists,
    get_user,
    UserData,
)
from app.services.bm25 import bm25_engine

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    token = authenticate(req.username, req.password)
    if not token:
        raise HTTPException(401, detail="Invalid credentials")
    user = get_user(req.username)
    return LoginResponse(
        token=token,
        first_name=user.first_name if user else None,
        last_name=user.last_name if user else None,
    )


@router.get("/users/{username}/exists")
def api_user_exists(username: str):
    return {"exists": user_exists(username)}


@router.post("/register", response_model=LoginResponse)
def register(req: RegisterRequest):
    try:
        register_user(
            req.username,
            req.password,
            req.first_name,
            req.last_name,
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

    token = authenticate(req.username, req.password)
    user = get_user(req.username)
    return LoginResponse(
        token=token,
        first_name=user.first_name,
        last_name=user.last_name,
    )

@router.get("/user/spaces")
def list_user_spaces(user: UserData = Depends(get_current_user)):
    return {"spaces": get_accessible_spaces(user.username)}

@router.post("/user/spaces")
def create_space(req: SpaceCreateRequest, user: UserData = Depends(get_current_user)):
    try:
        space_key = create_user_space(user.username, req.name)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    bm25_engine.index(str(space_key))
    return {"space": space_key}
