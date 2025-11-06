from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.v1.schemas import (
    SpaceCreateRequest,
    UserInfo,
)
from backend.app.dependencies import get_current_user
from backend.app.services.auth import (
    create_user_space,
    get_accessible_spaces,
    UserData,
)
from backend.app.services.search import search_engine

router = APIRouter()

# ============================================================================
# DEPRECATED ENDPOINTS - Supabase handles authentication
# ============================================================================
# The following endpoints are no longer used with Supabase auth:
# - POST /login -> Use Supabase Auth UI or supabase.auth.signInWithPassword()
# - POST /register -> Use Supabase Auth UI or supabase.auth.signUp()
# - GET /users/{username}/exists -> Use Supabase client methods
#
# These have been removed. Authentication is handled entirely by Supabase.
# The frontend gets a JWT token from Supabase, which the backend verifies.
# ============================================================================


# ============================================================================
# USER SPACE MANAGEMENT - Still active
# ============================================================================

@router.get("/user/info")
def get_user_info(user: UserData = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserInfo(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )


@router.get("/user/spaces")
def list_user_spaces(user: UserData = Depends(get_current_user)):
    """List all spaces accessible to the current user."""
    return {"spaces": get_accessible_spaces(user)}


@router.post("/user/spaces")
def create_space(req: SpaceCreateRequest, user: UserData = Depends(get_current_user)):
    """Create a new personal space for the current user."""
    try:
        space_key = create_user_space(user, req.name)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    search_engine.index(str(space_key))
    return {"space": space_key}
