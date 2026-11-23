from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field, StringConstraints
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

from ..services.case_retrieval import MAX_CASE_ID_LENGTH, fetch_case, search_cases

MCP_PATH = "/mcp"


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


def create_mcp_server() -> FastMCP:
    server = FastMCP(
        "Encuentra",
        instructions="Search and cite decisions of the Supreme Court of El Salvador.",
        streamable_http_path=MCP_PATH,
        stateless_http=True,
        json_response=True,
    )
    read_only = ToolAnnotations(readOnlyHint=True, openWorldHint=False)

    @server.tool(annotations=read_only)
    async def search(
        query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)],
    ) -> SearchOutput:
        """Find decisions matching a query in the Supreme Court corpus."""
        hits = await run_in_threadpool(search_cases, query)
        return SearchOutput(
            results=[SearchResult(id=hit.id, title=hit.title, url=hit.url) for hit in hits],
        )

    @server.tool(annotations=read_only)
    async def fetch(
        id: Annotated[str, Field(min_length=1, max_length=MAX_CASE_ID_LENGTH)],
    ) -> FetchOutput:
        """Read a decision by its search result ID. Check metadata.truncated for partial text."""
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
