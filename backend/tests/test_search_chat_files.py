import sys
from pathlib import Path
import io
import pytest

# Add backend directory to path for package imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.api.v1.endpoints import search as search_ep
from app.api.v1.endpoints import chat as chat_ep
from app.api.v1.endpoints import files as files_ep
from app.api.v1.schemas import ChatRequest
from app.services import auth
from app.services.bm25 import bm25_engine
from starlette.datastructures import UploadFile


@pytest.fixture()
def test_env(tmp_path, monkeypatch):
    """Prepare temp dirs, reset databases and index a small document."""
    monkeypatch.setattr(settings, "DATA_UPLOAD", str(tmp_path / "uploads"))
    monkeypatch.setattr(files_ep, "UPLOADS_ROOT", Path(settings.DATA_UPLOAD))
    files_ep.UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)

    # Reset auth DBs
    auth.users_db.clear()
    auth.orgs_db.clear()
    auth.tokens_db.clear()
    auth.init_data()
    user = auth.get_user("alice")
    user.spaces.append("supreme_court")
    monkeypatch.setattr(search_ep, "get_accessible_spaces", lambda u: ["supreme_court", "alice/personal"])

    # Reset BM25 engine
    bm25_engine.corpus.clear()
    bm25_engine.tokenized.clear()
    bm25_engine.bm25_models.clear()

    # Index the built-in supreme court corpus and a simple personal document
    bm25_engine.index("supreme_court")

    # Create a simple document in alice's personal space
    uploads_dir = Path(settings.DATA_UPLOAD) / "alice" / "personal"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "doc1.txt").write_text("hello world test document", encoding="utf-8")

    bm25_engine.index("alice/personal")
    return auth.get_user("alice")


def test_search_basic(test_env):
    user = test_env
    resp = search_ep.search(q="resolucion", top_k=3, space="supreme_court", user=user)
    assert resp.results
    hit = resp.results[0]
    assert hit.score > 0


def test_chat_basic(test_env):
    req = ChatRequest(question="resolucion?", space="supreme_court")
    resp = chat_ep.chat(req)
    assert isinstance(resp.answer, str) and resp.answer
    # At least one citation from the indexed corpus
    assert resp.citations


def test_file_upload_creates_file_and_indexes(test_env, monkeypatch):
    user = test_env
    uploaded = UploadFile(filename="new.txt", file=io.BytesIO(b"some content"))
    indexed = []

    def fake_index(space):
        indexed.append(space)

    monkeypatch.setattr(bm25_engine, "index", fake_index)

    import asyncio
    resp = asyncio.run(files_ep.upload_file(files=[uploaded], space="alice/personal", user=user))
    saved = resp["uploaded"][0]["saved_path"]
    path = Path(settings.DATA_UPLOAD) / "alice" / "personal" / saved
    assert path.exists()
    assert indexed == ["alice/personal"]

