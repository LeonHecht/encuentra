import logging
from typing import Annotated
from urllib.parse import urlsplit

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field, StringConstraints
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

from ..core.config import settings
from ..services.case_retrieval import (
    COURT_SPACE,
    DEFAULT_CASE_SEARCH_LIMIT,
    MAX_CASE_ID_LENGTH,
    fetch_case,
    search_cases,
)
from ..services.search_feedback import log_search_query
from .limits import MCPToolLimits

MCP_PATH = "/mcp"
logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    id: str
    title: str
    url: str


class SearchOutput(BaseModel):
    results: list[SearchResult]


class FetchMetadata(BaseModel):
    case_year: int | None
    truncated: bool


class FetchOutput(SearchResult):
    text: str
    metadata: FetchMetadata


def create_mcp_server(base_url: str) -> FastMCP:
    url = urlsplit(base_url)
    server = FastMCP(
        "Encuentra",
        instructions="Search and cite decisions of the Supreme Court of El Salvador.",
        streamable_http_path=MCP_PATH,
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            allowed_hosts=[url.netloc],
            allowed_origins=[f"{url.scheme}://{url.netloc}"],
        ),
    )
    limits = MCPToolLimits(settings.MCP_TOOL_CALLS_PER_MINUTE, settings.MCP_MAX_CONCURRENT_TOOL_CALLS)
    read_only = ToolAnnotations(readOnlyHint=True, openWorldHint=False)

    @server.tool(annotations=read_only)
    async def search(
        query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)],
    ) -> SearchOutput:
        """Find decisions matching a query in the Supreme Court corpus."""
        with limits.slot():
            hits = await run_in_threadpool(search_cases, query)
            result = SearchOutput(results=[SearchResult(id=hit.id, title=hit.title, url=hit.url) for hit in hits])
            try:
                await run_in_threadpool(
                    log_search_query,
                    user=None,
                    query_text=query,
                    space=COURT_SPACE,
                    top_k=DEFAULT_CASE_SEARCH_LIMIT,
                    year_filter=None,
                    result_count=len(result.results),
                    metadata={"source": "mcp"},
                )
            except Exception as exc:
                logger.warning("Anonymous MCP search logging failed (%s)", type(exc).__name__)
            return result

    @server.tool(annotations=read_only)
    async def fetch(
        id: Annotated[str, Field(min_length=1, max_length=MAX_CASE_ID_LENGTH)],
    ) -> FetchOutput:
        """Read a decision by its search result ID. Check metadata.truncated for partial text."""
        with limits.slot():
            decision = await run_in_threadpool(fetch_case, id)
        if decision is None:
            raise ToolError("Supreme Court decision not found.")
        return FetchOutput(
            id=decision.id,
            title=decision.title,
            url=decision.url,
            text=decision.text,
            metadata=FetchMetadata(case_year=decision.case_year, truncated=decision.truncated),
        )

    return server


class MCPStreamableHTTP:
    """Route the exact /mcp path to the SDK app created during FastAPI startup."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        mcp_app = getattr(scope["app"].state, "mcp_http_app", None)
        if mcp_app is None:
            await JSONResponse({"detail": "Not Found"}, status_code=404)(scope, receive, send)
            return
        await mcp_app(scope, receive, send)
