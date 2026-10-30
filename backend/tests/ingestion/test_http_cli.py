from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

import pytest
import requests

from backend.app.ingestion.asamblea import AsambleaSource
from backend.app.ingestion.http import HttpClient
from backend.app.jobs.scrape_legislation import main

HOST = "www.asamblea.gob.sv"
URL = f"https://{HOST}/leyes-y-decretos/view/4530"


class Clock:
    time = 0.0

    def __call__(self):
        return self.time

    def sleep(self, seconds):
        self.time += seconds


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = next(self.responses)
        response.url = url
        return response


def response(code=200, body=b"", headers=None):
    result = requests.Response()
    result.status_code, result._content, result._content_consumed = code, body, True
    result.headers.update(headers or {})
    return result


def client_with(responses, **kwargs):
    clock = Clock()
    session = Session(responses)
    return (
        HttpClient({HOST}, session=session, sleep=clock.sleep, clock=clock, **kwargs),
        session,
        clock,
    )


def test_throttle_and_429_retry_after():
    client, session, clock = client_with(
        [
            response(body=b"User-agent: *\nDisallow:\n"),
            response(429, headers={"Retry-After": "7"}),
            response(body=b"PDF"),
        ],
        interval=1.5,
    )
    assert client.get(URL).body == b"PDF"
    assert len(session.calls) == 3
    assert clock.time >= 8.5
    assert all(not kwargs["allow_redirects"] for _, kwargs in session.calls)


def test_http_date_retry_after():
    value = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=30), usegmt=True)
    assert 28 < HttpClient._retry_after(value) <= 30


def test_robots_is_enforced():
    client, session, clock = client_with(
        [response(body=b"User-agent: *\nDisallow: /leyes-y-decretos/\n")]
    )
    with pytest.raises(PermissionError):
        client.get(URL)
    assert len(session.calls) == 1


def test_robots_crawl_delay_is_respected():
    client, session, clock = client_with(
        [
            response(body=b"User-agent: *\nCrawl-delay: 5\n"),
            response(),
            response(),
        ],
        interval=1,
    )
    client.get(URL)
    client.get(URL)
    assert clock.time >= 6


def test_missing_robots_is_allowed_and_403_is_not_retried():
    client, session, clock = client_with([response(404), response(403)])
    with pytest.raises(requests.HTTPError):
        client.get(URL)
    assert len(session.calls) == 2


def test_redirects_cannot_escape_source_allowlist():
    client, session, clock = client_with(
        [response(), response(302, headers={"location": "https://other.invalid/file.pdf"})]
    )
    with pytest.raises(ValueError, match="allowlist"):
        client.get(URL)
    assert len(session.calls) == 2


def test_retry_exhaustion_and_download_limit():
    client, session, clock = client_with([response(), response(503), response(503)], attempts=2)
    with pytest.raises(requests.HTTPError):
        client.get(URL)
    client, session, clock = client_with([response(), response(body=b"oversized")], max_bytes=4)
    with pytest.raises(ValueError, match="exceeds"):
        client.get(URL)


def test_asamblea_intermediate_keeps_trusted_roots_and_cleans_temporary_bundle():
    import hashlib

    from cryptography import x509
    from cryptography.hazmat.primitives import serialization

    cert = AsambleaSource.extra_ca_file.read_bytes()
    der = x509.load_pem_x509_certificate(cert).public_bytes(serialization.Encoding.DER)
    assert (
        hashlib.sha256(der).hexdigest()
        == "6542d176bed50f193c0ce297ae44ecd8a0a86bec2ede682769344059b4e78530"
    )
    client = HttpClient({HOST}, extra_ca_file=AsambleaSource.extra_ca_file)
    bundle = Path(client.session.verify)
    assert bundle.read_bytes().startswith(Path(requests.certs.where()).read_bytes())
    assert bundle.read_bytes().endswith(cert)
    client.close()
    assert not bundle.exists()


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--years", "2026"],
        ["--years", "2026", "--output", "/tmp/corpus", "--prefix", "../escape"],
        ["--years", "2026", "--output", "/tmp/corpus", "--interval", "0"],
        ["--years", "2026", "--output", "/tmp/corpus", "--limit", "0"],
        ["--document-ids", "not-numeric", "--output", "/tmp/corpus"],
    ],
)
def test_cli_rejects_invalid_or_unbounded_scope(args, monkeypatch):
    monkeypatch.delenv("S3_BUCKET", raising=False)
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2
