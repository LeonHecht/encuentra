from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid
from pathlib import Path

from app.core.config import settings

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
tokens_db: Dict[str, str] = {}


def user_exists(username: str) -> bool:
    """Return True if *username* is present in the in-memory DB."""
    return username in users_db


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
    user = users_db.get(username)
    if not user or user.password != password:
        return None
    token = uuid.uuid4().hex
    tokens_db[token] = username
    return token


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


def create_user_space(username: str, name: str) -> Path:
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
    return resolved_dir

init_data()

