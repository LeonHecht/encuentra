from __future__ import annotations

import logging
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger(__name__)


@dataclass
class Response:
    url: str
    body: bytes
    headers: dict[str, str]
    status: int


class HttpClient:
    """Serial, bounded HTTP with per-host spacing, robots and explicit retries."""

    def __init__(
        self,
        allowed_hosts: set[str],
        *,
        interval: float = 1.5,
        attempts: int = 4,
        timeout: float = 45,
        max_bytes: int = 50 * 1024 * 1024,
        user_agent: str = "EncuentraCollector/1.0",
        session=None,
        sleep=time.sleep,
        clock=time.monotonic,
        extra_ca_file: Path | None = None,
    ):
        self.allowed_hosts = allowed_hosts
        self.interval = interval
        self.attempts = attempts
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.user_agent = user_agent
        self.session = session if session is not None else requests.Session()
        self._ca_directory = None
        if extra_ca_file is not None:
            # Supply a verified intermediate omitted by the remote TLS server.
            # Root trust and hostname verification remain enabled.
            self._ca_directory = tempfile.TemporaryDirectory(prefix="encuentra-ca-")
            bundle = Path(self._ca_directory.name) / "ca-bundle.pem"
            roots = Path(requests.certs.where()).read_bytes()
            bundle.write_bytes(roots + b"\n" + extra_ca_file.read_bytes())
            self.session.verify = str(bundle)
        self.sleep = sleep
        self.clock = clock
        self._next_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser] = {}

    def close(self):
        try:
            self.session.close()
        finally:
            if self._ca_directory is not None:
                self._ca_directory.cleanup()

    def validate_url(self, url: str) -> str:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in self.allowed_hosts
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
        ):
            raise ValueError(f"URL outside source allowlist: {url}")
        return parsed.netloc

    def _send(self, url: str, method: str = "GET", data: dict | None = None) -> Response:
        host = self.validate_url(url)
        for attempt in range(self.attempts):
            self.sleep(max(0, self._next_request.get(host, 0) - self.clock()))
            self._next_request[host] = self.clock() + self.interval
            retry_after = 0.0
            try:
                with getattr(self.session, method.lower())(
                    url,
                    headers={"User-Agent": self.user_agent},
                    timeout=(10, self.timeout),
                    allow_redirects=False,
                    stream=True,
                    **({"data": data} if method == "POST" else {}),
                ) as response:
                    if response.status_code in (408, 429, 500, 502, 503, 504):
                        retry_after = self._retry_after(response.headers.get("Retry-After"))
                        response.raise_for_status()
                    elif response.status_code != 404:
                        response.raise_for_status()
                    chunks, size = [], 0
                    for chunk in response.iter_content(64 * 1024):
                        size += len(chunk)
                        if size > self.max_bytes:
                            raise ValueError(f"Response exceeds {self.max_bytes} bytes: {url}")
                        chunks.append(chunk)
                    return Response(
                        url,
                        b"".join(chunks),
                        {k.lower(): v for k, v in response.headers.items()},
                        response.status_code,
                    )
            except requests.RequestException as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status is not None and status not in (408, 429, 500, 502, 503, 504):
                    raise
                if attempt + 1 == self.attempts:
                    raise
                delay = max(retry_after, min(60, 2**attempt))
                logger.warning("Retrying %s in %.1fs: %s", url, delay, exc)
                self.sleep(delay)
        raise RuntimeError("No HTTP attempts configured")

    @staticmethod
    def _retry_after(value: str | None) -> float:
        if not value:
            return 0
        try:
            return max(0, float(value))
        except ValueError:
            try:
                return max(
                    0, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()
                )
            except (ValueError, TypeError, OverflowError):
                return 0

    def _check_robots(self, url: str):
        parsed = urlsplit(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots:
            robots_url = origin + "/robots.txt"
            for _ in range(6):
                response = self._send(robots_url)
                if response.status in (301, 302, 303, 307, 308):
                    robots_url = urljoin(robots_url, response.headers["location"])
                    continue
                break
            else:
                raise RuntimeError("Too many robots.txt redirects")
            policy = RobotFileParser()
            # Missing robots is allowed; failures/403 are not silently ignored.
            policy.parse(
                []
                if response.status == 404
                else response.body.decode("utf-8", "replace").splitlines()
            )
            self._robots[origin] = policy
            delay = policy.crawl_delay(self.user_agent) or policy.crawl_delay("*") or 0
            self.interval = max(self.interval, delay)
            self._next_request[parsed.netloc] = max(
                self._next_request.get(parsed.netloc, 0),
                self.clock() + delay,
            )
        if not self._robots[origin].can_fetch(self.user_agent, url):
            raise PermissionError(f"robots.txt disallows {url}")

    def _request(self, url: str, method: str = "GET", data: dict | None = None) -> Response:
        for _ in range(6):
            self.validate_url(url)
            self._check_robots(url)
            response = self._send(url, method, data)
            if response.status in (301, 302, 303, 307, 308):
                url = urljoin(url, response.headers["location"])
                if response.status == 303 or (method == "POST" and response.status in (301, 302)):
                    method, data = "GET", None
                continue
            if response.status == 404:
                raise FileNotFoundError(url)
            return response
        raise RuntimeError("Too many redirects")

    def get(self, url: str) -> Response:
        return self._request(url)

    def post(self, url: str, *, data: dict) -> Response:
        """Form POST for read-only catalog queries, using the same retry/rate policy."""
        return self._request(url, "POST", data)
