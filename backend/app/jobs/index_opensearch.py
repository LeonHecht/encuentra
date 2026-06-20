from __future__ import annotations

import argparse
import json

from backend.app.core.config import settings
from backend.app.services.search import search_engine


def main() -> None:
    parser = argparse.ArgumentParser(description="Incrementally index S3 text files into OpenSearch.")
    parser.add_argument("space", nargs="?", default="supreme_court")
    parser.add_argument(
        "--delete-missing",
        action="store_true",
        help="Delete indexed S3 documents whose source text key is no longer present under S3_TEXT_PREFIX.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=500,
        help="Print progress after this many S3 text files are seen.",
    )
    args = parser.parse_args()

    if settings.SEARCH_BACKEND.lower() != "opensearch":
        raise RuntimeError("Incremental indexing requires SEARCH_BACKEND=opensearch.")
    if not hasattr(search_engine, "index_incremental"):
        raise RuntimeError("The active search backend does not support incremental indexing.")

    stats = search_engine.index_incremental(
        args.space,
        delete_missing=args.delete_missing,
        progress_every=args.progress_every,
    )
    print(json.dumps(stats, sort_keys=True))


if __name__ == "__main__":
    main()