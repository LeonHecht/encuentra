from pathlib import Path
from unittest.mock import MagicMock, patch
import uuid

import pytest

from backend.app.core.config import settings
import backend.app.services.auth as auth
from backend.app.core.security import tokens_db


@pytest.fixture()
def auth_env(tmp_path, monkeypatch):
    """Reset in-memory databases and prepare temp upload directory."""
    monkeypatch.setattr(settings, "DATA_UPLOAD", str(tmp_path))
    auth.users_db.clear()
    auth.orgs_db.clear()
    tokens_db.clear()
    auth.init_data()
    return tmp_path


@pytest.fixture()
def mock_supabase(monkeypatch):
    """Mock Supabase client for testing."""
    mock_client = MagicMock()
    
    # Mock table responses
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    
    # Setup default empty responses
    mock_response = MagicMock()
    mock_response.data = []
    
    mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
    mock_table.insert.return_value.execute.return_value = mock_response
    
    # Mock the get_supabase function to return our mock client
    monkeypatch.setattr(auth, "get_supabase", lambda: mock_client)
    
    return mock_client


# ============================================================================
# Tests for new Supabase authentication
# ============================================================================

def test_get_or_create_user_from_supabase_new_user(auth_env, mock_supabase):
    """Test creating a new user from Supabase JWT data."""
    user_id = str(uuid.uuid4())
    email = "test@example.com"
    user_metadata = {"first_name": "Test", "last_name": "User"}
    
    # Mock empty response (user doesn't exist)
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    # Mock successful insert
    mock_insert_response = MagicMock()
    mock_insert_response.data = [{"id": user_id, "display_name": "Test User"}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_response
    
    # Create user
    user = auth.get_or_create_user_from_supabase(user_id, email, user_metadata)
    
    # Assertions
    assert user.username == email
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert "personal" in user.spaces
    
    # Verify Supabase calls
    assert mock_supabase.table.call_count >= 2  # user_profiles + spaces
    
    # Verify upload directory was created
    upload_dir = Path(settings.DATA_UPLOAD) / email / "personal"
    assert upload_dir.exists() and upload_dir.is_dir()


def test_get_or_create_user_from_supabase_existing_user(auth_env, mock_supabase):
    """Test retrieving an existing user from Supabase."""
    user_id = str(uuid.uuid4())
    email = "existing@example.com"
    
    # Mock existing user profile
    mock_profile_response = MagicMock()
    mock_profile_response.data = [{
        "id": user_id,
        "display_name": "Existing User"
    }]
    
    # Mock existing spaces
    mock_spaces_response = MagicMock()
    mock_spaces_response.data = [
        {"name": "personal"},
        {"name": "work"}
    ]
    
    # Mock org membership (none)
    mock_org_response = MagicMock()
    mock_org_response.data = []
    
    # Setup mock to return different responses for different calls
    def mock_execute(*args, **kwargs):
        # First call: user_profiles query
        if not hasattr(mock_execute, 'call_count'):
            mock_execute.call_count = 0
        mock_execute.call_count += 1
        
        if mock_execute.call_count == 1:
            return mock_profile_response
        elif mock_execute.call_count == 2:
            return mock_spaces_response
        else:
            return mock_org_response
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = mock_execute
    
    # Get user
    user = auth.get_or_create_user_from_supabase(user_id, email)
    
    # Assertions
    assert user.username == email
    assert user.spaces == ["personal", "work"]
    assert user.organization is None


def test_get_or_create_user_from_supabase_with_org(auth_env, mock_supabase):
    """Test user with organization membership."""
    user_id = str(uuid.uuid4())
    email = "org_user@example.com"
    org_id = str(uuid.uuid4())
    
    # Mock existing user profile
    mock_profile_response = MagicMock()
    mock_profile_response.data = [{
        "id": user_id,
        "display_name": "Org User"
    }]
    
    # Mock spaces
    mock_spaces_response = MagicMock()
    mock_spaces_response.data = [{"name": "personal"}]
    
    # Mock org membership
    mock_org_response = MagicMock()
    mock_org_response.data = [{"org_id": org_id}]
    
    call_count = 0
    def mock_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_profile_response
        elif call_count == 2:
            return mock_spaces_response
        else:
            return mock_org_response
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = mock_execute
    
    # Get user
    user = auth.get_or_create_user_from_supabase(user_id, email)
    
    # Assertions
    assert user.organization == org_id


# ============================================================================
# Tests for legacy authentication (deprecated but kept for backward compat)
# ============================================================================

def test_authenticate_deprecated(auth_env):
    """Test that deprecated authenticate() returns None."""
    # authenticate() is now deprecated and returns None
    token = auth.authenticate("alice", "alice")
    assert token is None


def test_get_accessible_spaces(auth_env):
    """Test getting accessible spaces for a user."""
    spaces = auth.get_accessible_spaces("alice")
    assert "alice/personal" in spaces
    assert "demo_org/shared" in spaces
    assert "supreme_court" in spaces  # Public space


def test_create_user_space_valid(auth_env):
    """Test creating a valid user space."""
    space_key = auth.create_user_space("alice", "newspace")
    expected = Path(settings.DATA_UPLOAD) / "alice" / "newspace"
    assert expected.exists() and expected.is_dir()
    assert space_key == "alice/newspace"


def test_create_user_space_invalid(auth_env):
    """Test that invalid space names are rejected."""
    with pytest.raises(ValueError, match="Invalid space name"):
        auth.create_user_space("alice", "../bad")
    with pytest.raises(ValueError, match="Invalid space name"):
        auth.create_user_space("alice", "bad/name")
    with pytest.raises(ValueError, match="Invalid space name"):
        auth.create_user_space("alice", "bad\\name")


def test_user_exists_and_get_user(auth_env):
    """Test user existence check and retrieval."""
    assert auth.user_exists("alice")
    assert not auth.user_exists("bob")
    user = auth.get_user("alice")
    assert user and user.username == "alice"


def test_register_user(auth_env):
    """Test registering a new user (legacy method)."""
    new_user = auth.register_user("bob", "secret", "Bob", "Builder")
    assert new_user.username == "bob"
    assert new_user.first_name == "Bob"
    assert auth.user_exists("bob")
    # personal upload dir created
    path = Path(settings.DATA_UPLOAD) / "bob" / "personal"
    assert path.exists() and path.is_dir()


def test_register_user_duplicate(auth_env):
    """Test that registering a duplicate user raises an error."""
    with pytest.raises(ValueError, match="User already exists"):
        auth.register_user("alice", "pass")
