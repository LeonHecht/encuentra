from dataclasses import dataclass, field
from typing import Dict, List, Optional
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


# Spaces that are accessible to all users
PUBLIC_SPACES = ["supreme_court"]
@dataclass
class UserData:
    username: str
    password: str
    first_name: str = ""
    last_name: str = ""
    spaces: List[str] = field(default_factory=list)
    organization: Optional[str] = None

@dataclass
class OrgData:
    name: str
    spaces: List[str] = field(default_factory=list)
    members: List[str] = field(default_factory=list)

users_db: Dict[str, UserData] = {}
orgs_db: Dict[str, OrgData] = {}


def user_exists(username: str) -> bool:
    """Return True if *username* is present in the in-memory DB.
    
    NOTE: With Supabase, user existence is handled by Supabase Auth.
    This function is kept for backward compatibility but may not be needed.
    """
    return username in users_db


# DEPRECATED: Supabase handles user registration
# Keeping for backward compatibility, but should migrate to Supabase
def register_user(username: str, password: str, first_name: str = "", last_name: str = "") -> UserData:
    """Create a new user and return the created ``UserData``.

    Raises ``ValueError`` if the user already exists.
    """
    if username in users_db:
        raise ValueError("User already exists")

    user = UserData(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        spaces=["personal"],
    )
    users_db[username] = user
    # create upload directory for the personal space
    Path(settings.DATA_UPLOAD, username, "personal").mkdir(parents=True, exist_ok=True)
    return user


def get_user(username: str) -> Optional[UserData]:
    """Return ``UserData`` for *username* or ``None``."""
    return users_db.get(username)


def get_or_create_user_from_supabase(user_id: str, email: str, user_metadata: Optional[dict] = None) -> UserData:
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
        sb = get_supabase()
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
                username=email,
                password="",  # Not needed with Supabase
                first_name=user_metadata.get("first_name", "") if user_metadata else "",
                last_name=user_metadata.get("last_name", "") if user_metadata else "",
                spaces=space_names,
                organization=organization,
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
                username=email,
                password="",
                first_name=user_metadata.get("first_name", "") if user_metadata else "",
                last_name=user_metadata.get("last_name", "") if user_metadata else "",
                spaces=["personal"],
                organization=None,
            )
    except Exception as e:
        print(f"Error getting/creating user from Supabase: {e}")
        raise ValueError(f"Failed to get or create user: {str(e)}")
    

def init_data() -> None:
    """Initialize a few demo users and organizations."""
    if users_db:
        return

    org = OrgData(name="demo_org", spaces=["shared"])
    orgs_db[org.name] = org

    user = UserData(username="alice", password="alice", spaces=["personal"], organization=org.name)
    users_db[user.username] = user
    org.members.append(user.username)

    for space in user.spaces:
        Path(settings.DATA_UPLOAD, user.username, space).mkdir(parents=True, exist_ok=True)
    for space in org.spaces:
        Path(settings.DATA_UPLOAD, org.name, space).mkdir(parents=True, exist_ok=True)


def authenticate(username: str, password: str) -> Optional[str]:
    """DEPRECATED: Authentication is now handled by Supabase.
    
    This function is kept for backward compatibility but should not be used
    with Supabase auth. Instead, validate Supabase JWT tokens.
    """
    # This function is no longer used with Supabase auth
    # Keeping it here to avoid breaking existing code during migration
    return None


def get_accessible_spaces(username: str) -> List[str]:
    user = users_db.get(username)
    if not user:
        print(f"WARNING: User {username} not found")
        return PUBLIC_SPACES.copy()
    print(f"DEGUB: User {username} found with spaces: {user.spaces}")
    spaces = [f"{user.username}/{s}" for s in user.spaces]
    if user.organization and user.organization in orgs_db:
        spaces += [f"{user.organization}/{s}" for s in orgs_db[user.organization].spaces]
    return PUBLIC_SPACES + spaces


def create_user_space(username: str, name: str) -> str:
    """Create a directory for *name* under the given user's upload space.
    Reject ``name`` values containing path traversal characters and ensure the
    directory is created inside ``settings.DATA_UPLOAD/<username>/``.
    """
    # Reject dangerous names
    if any(token in name for token in ("..", "/", "\\")):
        raise ValueError("Invalid space name")

    uploads_root = Path(settings.DATA_UPLOAD) / username
    uploads_root.mkdir(parents=True, exist_ok=True)

    space_dir = uploads_root / name

    # Resolve paths to ensure the result stays within uploads_root
    resolved_root = uploads_root.resolve()
    resolved_dir = space_dir.resolve()
    if not resolved_dir.is_relative_to(resolved_root):
        raise ValueError("Invalid directory path")

    resolved_dir.mkdir(parents=True, exist_ok=True)

    # put the new personal space into the user profile
    user = users_db.get(username)
    if user and name not in user.spaces:
        user.spaces.append(name)
    # Return plain string "alice/newspace" instead of Path,
    # because that's what the rest of the API expects.
    return f"{username}/{name}"

init_data()

