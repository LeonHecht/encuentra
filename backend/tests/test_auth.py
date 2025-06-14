import sys
from pathlib import Path

import pytest

# Add backend directory to path for package imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings
import app.services.auth as auth


@pytest.fixture()
def auth_env(tmp_path, monkeypatch):
    """Reset in-memory databases and prepare temp upload directory."""
    monkeypatch.setattr(settings, "DATA_UPLOAD", str(tmp_path))
    auth.users_db.clear()
    auth.orgs_db.clear()
    auth.tokens_db.clear()
    auth.init_data()
    return tmp_path


def test_authenticate_success(auth_env):
    token = auth.authenticate("alice", "alice")
    assert token
    assert auth.tokens_db[token] == "alice"


def test_authenticate_wrong_password(auth_env):
    assert auth.authenticate("alice", "wrong") is None


def test_authenticate_unknown_user(auth_env):
    assert auth.authenticate("bob", "whatever") is None


def test_get_accessible_spaces(auth_env):
    spaces = auth.get_accessible_spaces("alice")
    assert "alice/personal" in spaces
    assert "demo_org/shared" in spaces


def test_create_user_space_valid(auth_env):
    path = auth.create_user_space("alice", "newspace")
    assert path.exists() and path.is_dir()
    expected = Path(settings.DATA_UPLOAD) / "alice" / "newspace"
    assert path == expected


def test_create_user_space_invalid(auth_env):
    with pytest.raises(ValueError):
        auth.create_user_space("alice", "../bad")
    with pytest.raises(ValueError):
        auth.create_user_space("alice", "bad/name")
    with pytest.raises(ValueError):
        auth.create_user_space("alice", "bad\\name")


def test_user_exists_and_get_user(auth_env):
    assert auth.user_exists("alice")
    assert not auth.user_exists("bob")
    user = auth.get_user("alice")
    assert user and user.username == "alice"


def test_register_user(auth_env):
    new_user = auth.register_user("bob", "secret", "Bob", "Builder")
    assert new_user.username == "bob"
    assert new_user.first_name == "Bob"
    assert auth.user_exists("bob")
    # personal upload dir created
    path = Path(settings.DATA_UPLOAD) / "bob" / "personal"
    assert path.exists() and path.is_dir()


def test_register_user_duplicate(auth_env):
    with pytest.raises(ValueError):
        auth.register_user("alice", "pass")
