from collections import deque
from contextlib import contextmanager
from math import ceil
from time import monotonic

from mcp.server.fastmcp.exceptions import ToolError


class MCPToolLimits:
    """Bound admitted tool calls in the FastAPI worker's event loop."""

    def __init__(self, calls_per_minute: int, max_concurrent: int) -> None:
        self._calls_per_minute = calls_per_minute
        self._max_concurrent = max_concurrent
        self._started: deque[float] = deque()
        self._in_flight = 0

    @contextmanager
    def slot(self):
        now = monotonic()
        while self._started and self._started[0] <= now - 60:
            self._started.popleft()

        if len(self._started) >= self._calls_per_minute:
            retry_after = max(1, ceil(self._started[0] + 60 - now))
            raise ToolError(f"MCP tool rate limit reached. Retry after {retry_after}s.")
        if self._in_flight >= self._max_concurrent:
            raise ToolError("Encuentra is processing too many MCP tool calls. Retry in a few seconds.")

        self._started.append(now)
        self._in_flight += 1
        try:
            yield
        finally:
            self._in_flight -= 1
