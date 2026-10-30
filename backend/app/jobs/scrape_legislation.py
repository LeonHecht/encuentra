"""Collect legislation without importing FastAPI, settings or OpenSearch."""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
from pathlib import Path

from backend.app.ingestion.asamblea import AsambleaSource
from backend.app.ingestion.diario_oficial import DiarioOficialSource
from backend.app.ingestion.http import HttpClient
from backend.app.ingestion.pipeline import Collector
from backend.app.ingestion.storage import LocalStore, S3Store, checked_key

# Add the judicial portal here when its adapter is ready.
SOURCES = {"asamblea": AsambleaSource, "diario_oficial": DiarioOficialSource}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=SOURCES, default="asamblea")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--years", nargs="+", type=int)
    scope.add_argument("--all-years", action="store_true")
    scope.add_argument("--document-ids", nargs="+")
    parser.add_argument(
        "--months", nargs="+", type=int, help="Diario Oficial: filter advertised months (1–12)"
    )
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--output", type=Path, help="Local destination, no AWS access")
    destination.add_argument(
        "--bucket", help="S3 bucket; defaults to S3_BUCKET environment variable"
    )
    parser.add_argument(
        "--prefix", default="legislation", help="Separate destination prefix for this corpus"
    )
    parser.add_argument(
        "--limit", type=int, help="Maximum records considered, including skipped records"
    )
    parser.add_argument(
        "--refresh", action="store_true", help="Re-fetch completed records to detect changes"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.5,
        help="Minimum seconds between request starts per host",
    )
    parser.add_argument("--attempts", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--max-download-mb", type=int, default=50)
    parser.add_argument("--min-page-characters", type=int, default=20)
    parser.add_argument("--user-agent", default="EncuentraCollector/1.0")
    args = parser.parse_args(argv)
    if (
        not math.isfinite(args.interval)
        or not math.isfinite(args.timeout)
        or args.interval < 1
        or args.attempts < 1
        or args.timeout <= 0
        or args.max_download_mb < 1
        or args.min_page_characters < 1
        or (args.limit is not None and args.limit < 1)
    ):
        parser.error(
            "interval must be >= 1; attempts, timeout, download size, page characters and limit must be positive"
        )
    if args.years and any(y < 1 or y > 9999 for y in args.years):
        parser.error("years must be between 1 and 9999")
    if args.months and (
        args.source != "diario_oficial"
        or args.document_ids
        or any(not 1 <= m <= 12 for m in args.months)
    ):
        parser.error(
            "--months requires diario_oficial with --years/--all-years, and months between 1 and 12"
        )
    try:
        prefix = checked_key(args.prefix)
    except ValueError as exc:
        parser.error(str(exc))
    bucket = args.bucket or os.getenv("S3_BUCKET")
    if args.output:
        store = LocalStore(args.output / prefix)
    elif bucket:
        store = S3Store(bucket, prefix)
    else:
        parser.error("Choose --output or --bucket (or set S3_BUCKET)")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    source = SOURCES[args.source]()
    if args.document_ids:
        try:
            refs = [source.reference(i) for i in dict.fromkeys(args.document_ids)]
        except ValueError as exc:
            parser.error(str(exc))
    client = HttpClient(
        source.allowed_hosts,
        interval=args.interval,
        attempts=args.attempts,
        timeout=args.timeout,
        max_bytes=args.max_download_mb * 1024 * 1024,
        user_agent=args.user_agent,
        extra_ca_file=getattr(source, "extra_ca_file", None),
    )
    try:
        if not args.document_ids:
            refs = source.discover(
                client, args.years, **({"months": args.months} if args.months else {})
            )
        report = Collector(source, client, store, min_page_characters=args.min_page_characters).run(
            refs,
            refresh=args.refresh,
            limit=args.limit,
        )
        print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
        return 130 if report["status"] == "interrupted" else int(report["status"] != "complete")
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
