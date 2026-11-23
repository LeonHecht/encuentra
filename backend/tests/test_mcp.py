import asyncio
import json
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from opensearchpy.exceptions import NotFoundError
from pydantic import AnyHttpUrl

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.services.case_retrieval import MAX_DECISION_CHARS
from backend.app.services.opensearch import opensearch_engine
from backend.app.services.search import search_engine


LOCAL_ORIGIN = "http://127.0.0.1:8000"


def test_mcp_streamable_http_search_and_fetch(monkeypatch):
    monkeypatch.setattr(settings, "MCP_ENABLED", True)
    monkeypatch.setattr(settings, "CASE_CITATION_BASE_URL", AnyHttpUrl(LOCAL_ORIGIN))
    monkeypatch.setattr(settings, "OPENSEARCH_INDEX_PREFIX", "encuentra-test")
    document = {"id": "42-2024", "title": "Derecho de audiencia", "case_year": 2024}
    index = Mock()
    index.indices.exists_alias.return_value = True
    index.search.return_value = {"hits": {"hits": [{"_id": document["id"], "_source": document}]}}
    indexed_text = "Resolución sobre el derecho de audiencia. " * 500
    index.get.return_value = {"_source": {**document, "text": indexed_text}}
    monkeypatch.setattr(opensearch_engine, "_get_client", lambda: index)

    async def check_tools():
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=LOCAL_ORIGIN) as http:
                async with streamable_http_client(f"{LOCAL_ORIGIN}/mcp", http_client=http) as (read, write, session_id):
                    async with ClientSession(read, write) as session:
                        handshake = await session.initialize()
                        assert handshake.serverInfo.name == "Encuentra"
                        assert session_id() is None
                        tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                        assert tools.keys() == {"search", "fetch"}
                        assert tools["search"].inputSchema["required"] == ["query"]
                        assert tools["fetch"].inputSchema["required"] == ["id"]
                        assert tools["search"].outputSchema["required"] == ["results"]
                        assert set(tools["fetch"].outputSchema["required"]) >= {"id", "title", "text", "url"}
                        assert all(tool.annotations.readOnlyHint for tool in tools.values())

                        result = await session.call_tool("search", {"query": "audiencia"})
                        assert not result.isError
                        hit = result.structuredContent["results"][0]
                        assert hit == {
                            "id": "42-2024",
                            "title": "Derecho de audiencia",
                            "url": f"{LOCAL_ORIGIN}/cases/supreme-court?id=42-2024",
                        }
                        assert json.loads(result.content[0].text) == result.structuredContent
                        assert index.search.call_args.kwargs["index"] == "encuentra-test-supreme_court"

                        result = await session.call_tool("fetch", {"id": hit["id"]})
                        assert not result.isError
                        assert result.structuredContent == {
                            **hit,
                            "text": indexed_text,
                            "metadata": {"case_year": 2024, "truncated": False},
                        }
                        assert json.loads(result.content[0].text) == result.structuredContent
                        index.get.assert_called_once_with(index="encuentra-test-supreme_court", id=hit["id"])
                        citation_page = await http.get(hit["url"])
                        assert citation_page.status_code == 200
                        assert indexed_text in citation_page.text

                        long_text = "x" * (MAX_DECISION_CHARS + 1)
                        index.get.return_value = {"_source": {**document, "text": long_text}}
                        result = await session.call_tool("fetch", {"id": hit["id"]})
                        assert result.structuredContent["text"] == long_text[:MAX_DECISION_CHARS]
                        assert result.structuredContent["metadata"]["truncated"] is True

                        index.get.side_effect = NotFoundError(404, "not_found", {})
                        result = await session.call_tool("fetch", {"id": "missing"})
                        assert result.isError
                        assert "decision not found" in result.content[0].text

    asyncio.run(check_tools())
    with TestClient(app, base_url=LOCAL_ORIGIN) as client:
        response = client.post(
            "/mcp",
            headers={"Accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "restart-test", "version": "1"},
                },
            },
        )
        assert response.status_code == 200
        assert response.json()["result"]["serverInfo"]["name"] == "Encuentra"
        assert client.get("/ping").json() == {"status": "pong"}


def test_mcp_disabled_preserves_startup_indexing(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MCP_ENABLED", False)
    monkeypatch.setattr(settings, "INDEX_ON_STARTUP", True)
    monkeypatch.setattr(settings, "SKIP_REINDEX_ON_STARTUP", False)
    monkeypatch.setattr(settings, "DATA_UPLOAD", str(tmp_path))
    index = Mock()
    monkeypatch.setattr(search_engine, "index", index)

    with TestClient(app, base_url=LOCAL_ORIGIN) as client:
        assert client.post("/mcp").status_code == 404
        assert client.get("/ping").json() == {"status": "pong"}

    index.assert_called_once_with(space="supreme_court")


def test_mcp_requires_citation_origin_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "MCP_ENABLED", True)
    monkeypatch.setattr(settings, "CASE_CITATION_BASE_URL", None)

    with pytest.raises(RuntimeError, match="CASE_CITATION_BASE_URL"):
        with TestClient(app, base_url=LOCAL_ORIGIN):
            pass
