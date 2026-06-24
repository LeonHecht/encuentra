from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .services.auth import get_or_create_user_from_supabase, UserData
from .core.security import verify_supabase_token

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserData:
    """
    Dependency that extracts and verifies the Supabase JWT token.
    Returns the current user's data from Supabase database.
    """
    token = credentials.credentials
    
    try:
        # Verify the Supabase JWT token
        payload = verify_supabase_token(token)
        
        # Extract user info from token
        user_id = payload.get("sub")
        email = payload.get("email")
        user_metadata = payload.get("user_metadata", {})
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id or email",
            )
        
        # Get or create user in database. If Supabase has a transient connection
        # failure, keep authenticated public-space requests working from the
        # verified JWT. Private spaces still require get_accessible_spaces to
        # reach Supabase.
        try:
            return get_or_create_user_from_supabase(user_id, email, user_metadata)
        except Exception as e:
            print(f"User profile lookup failed; using JWT-only user context: {e}")
            return UserData(
                user_id=user_id,
                username=email,
                first_name=user_metadata.get("first_name", "") if user_metadata else "",
                last_name=user_metadata.get("last_name", "") if user_metadata else "",
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )