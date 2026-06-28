from dataclasses import dataclass, field
from typing import List, Optional
from supabase import create_client, Client
from pathlib import Path
from threading import Lock

from ..core.config import settings

# Lazy-initialized Supabase client
_supabase_client: Optional[Client] = None
_supabase_lock = Lock()


def get_supabase() -> Client:
    """Return a singleton Supabase client. Created on first use (thread-safe)."""
    global _supabase_client
    if _supabase_client is None:
        with _supabase_lock:
            # Double-check pattern: another thread might have initialized while we waited
            if _supabase_client is None:
                url = settings.SUPABASE_URL
                key = settings.SUPABASE_KEY
                if not url or not key:
                    raise RuntimeError("Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in .env")
                _supabase_client = create_client(url, key)
    return _supabase_client


PUBLIC_SPACES = ["supreme_court"]

@dataclass
class UserData:
    """Represents the authenticated user context derived from Supabase.

    Fields:
        user_id: Supabase auth.users UUID (sub claim)
        username: Email (kept for backward compatibility with existing code that expects `username`)
        first_name / last_name: From JWT user_metadata if present
        spaces: Names of personal spaces already indexed (not authoritative; convenience only)
        organization: Single org UUID if membership exists (simplified)
    """
    user_id: str
    username: str  # email
    first_name: str = ""
    last_name: str = ""
    spaces: List[str] = field(default_factory=list)
    organization: Optional[str] = None
    access_token: Optional[str] = None


def get_supabase_for_user(user: UserData) -> Client:
    """Return Supabase client with the caller JWT applied when available.

    Backend deployments commonly use either a service-role key, which bypasses
    RLS, or an anon key, which needs the user's JWT for RLS-protected tables.
    Applying the JWT here keeps both configurations returning the same rows.
    """
    return get_supabase_with_token(getattr(user, "access_token", None))


def get_supabase_with_token(token: Optional[str]) -> Client:
    """Return a Supabase client scoped to a caller JWT when provided."""
    if not token:
        return get_supabase()

    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        raise RuntimeError("Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in .env")
    sb = create_client(url, key)
    apply_supabase_auth(sb, token)
    return sb


def apply_supabase_auth(sb: Client, token: Optional[str]) -> None:
    """Apply a caller JWT to Supabase PostgREST when the client supports it."""
    if token:
        postgrest = getattr(sb, "postgrest", None)
        auth_method = getattr(postgrest, "auth", None)
        if callable(auth_method):
            auth_method(token)


def get_or_create_user_from_supabase(
    user_id: str,
    email: str,
    user_metadata: Optional[dict] = None,
    access_token: Optional[str] = None,
) -> UserData:
    """
    Get or create a user from Supabase JWT token data.
    This replaces the in-memory users_db with Supabase database.
    
    Args:
        user_id: Supabase user UUID (from JWT 'sub' claim)
        email: User's email (from JWT 'email' claim)
        user_metadata: Additional metadata from JWT (first_name, last_name, etc.)
    
    Returns:
        UserData object with user information
    """
    # Check if user profile exists in Supabase
    try:
        sb = get_supabase_with_token(access_token)
        response = sb.table("user_profiles").select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            # User exists, return their data
            profile = response.data[0]
            
            # Get user's spaces
            spaces_response = sb.table("spaces").select("name").eq("owner_id", user_id).execute()
            space_names = [s["name"] for s in spaces_response.data] if spaces_response.data else ["personal"]
            
            # Check if user belongs to any organization
            org_membership = sb.table("members").select("org_id").eq("user_id", user_id).execute()
            organization = org_membership.data[0]["org_id"] if org_membership.data else None
            
            return UserData(
                user_id=user_id,
                username=email,
                first_name=user_metadata.get("first_name", "") if user_metadata else "",
                last_name=user_metadata.get("last_name", "") if user_metadata else "",
                spaces=space_names,
                organization=organization,
                access_token=access_token,
            )
        else:
            # User doesn't exist, create profile
            print(f"Creating new user profile for {email}")
            
            # 1. Create user_profile (only with fields that exist in schema)
            sb.table("user_profiles").insert({
                "id": user_id,
                "display_name": user_metadata.get("full_name") if user_metadata else email,
            }).execute()
            
            # 2. Create default "personal" space
            sb.table("spaces").insert({
                "name": "personal",
                "owner_id": user_id,
                "is_public": False,
            }).execute()
            
            # 3. Create local upload directory
            upload_dir = Path(settings.DATA_UPLOAD) / email / "personal"
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"✅ User profile created for {email}")
            
            return UserData(
                user_id=user_id,
                username=email,
                first_name=user_metadata.get("first_name", "") if user_metadata else "",
                last_name=user_metadata.get("last_name", "") if user_metadata else "",
                spaces=["personal"],
                organization=None,
                access_token=access_token,
            )
    except Exception as e:
        print(f"Error getting/creating user from Supabase: {e}")
        raise ValueError(f"Failed to get or create user: {str(e)}")
    

def get_accessible_spaces(user: UserData) -> List[str]:
    """Return a list of space identifiers the user can access.

    Format matches existing frontend expectations:
        - Public spaces: "supreme_court" (no slash)
        - Personal spaces: "<email>/<space_name>"
        - Org spaces: "<org_id>/<space_name>" (can later be swapped to org name)
    """
    spaces = PUBLIC_SPACES.copy()

    # Keep profile-derived spaces as a fallback. These are raw names from the
    # spaces table, while API-facing identifiers include the owner email.
    for space_name in user.spaces:
        if "/" in space_name:
            spaces.append(space_name)
        else:
            spaces.append(f"{user.username}/{space_name}")

    try:
        sb = get_supabase_for_user(user)
    except Exception as e:
        print(f"get_accessible_spaces client error: {e}", flush=True)
        return list(dict.fromkeys(spaces))

    try:
        owned_resp = sb.table("spaces").select("name").eq("owner_id", user.user_id).execute()
        if owned_resp.data:
            spaces.extend(f"{user.username}/{row['name']}" for row in owned_resp.data)
    except Exception as e:
        print(f"get_accessible_spaces owned spaces error: {e}", flush=True)

    try:
        membership_resp = sb.table("members").select("org_id").eq("user_id", user.user_id).execute()
        org_ids = [m["org_id"] for m in membership_resp.data] if membership_resp.data else []
    except Exception as e:
        print(f"get_accessible_spaces memberships error: {e}", flush=True)
        org_ids = []

    for oid in org_ids:
        try:
            s_resp = sb.table("spaces").select("name").eq("org_id", oid).execute()
            if s_resp.data:
                spaces.extend(f"{oid}/{row['name']}" for row in s_resp.data)
        except Exception as e:
            print(f"get_accessible_spaces org spaces error for {oid}: {e}", flush=True)

    return list(dict.fromkeys(spaces))  # preserve order, de-dup


def create_user_space(user: UserData, name: str) -> str:
    """Create a new personal space for the user in Supabase and local FS.

    Safeguards against traversal and ensures directory creation under DATA_UPLOAD/<email>/<space>.
    Returns identifier '<email>/<space>'.
    """
    if any(token in name for token in ("..", "/", "\\")):
        raise ValueError("Invalid space name")
    try:
        sb = get_supabase_for_user(user)
        # Insert space row (id auto-generated). Avoid duplicates.
        existing = sb.table("spaces").select("name").eq("owner_id", user.user_id).eq("name", name).execute()
        if not (existing.data and len(existing.data) > 0):
            sb.table("spaces").insert({
                "name": name,
                "owner_id": user.user_id,
                "is_public": False,
            }).execute()
        # local directory
        uploads_root = Path(settings.DATA_UPLOAD) / user.username
        space_dir = uploads_root / name
        space_dir.mkdir(parents=True, exist_ok=True)
        # Update in-memory convenience list (not authoritative)
        if name not in user.spaces:
            user.spaces.append(name)
        return f"{user.username}/{name}"
    except Exception as e:
        raise ValueError(f"Failed to create space: {e}")
