from pathlib import Path
from app.core.config import settings


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
