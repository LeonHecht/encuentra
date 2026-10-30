# Legislation collection

The standalone collector supports **Asamblea Legislativa** (`asamblea`) and
**Diario Oficial** (`diario_oficial`). It discovers source catalogs, preserves
metadata, downloads PDFs and extracts page-addressable text. Asamblea annual
catalogs include laws, reforms and other decrees, retained as individual records.
Diario Oficial records are complete editions or historical archive parts, which
can contain many laws and other notices. Collection does not determine legal
validity, consolidate laws, or split gazettes into individual laws.

Run commands from the **repository root**, with Python 3.10+:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-scraping.txt

# Bounded pilot, entirely local. No API, AWS or OpenSearch connection is needed.
python -m backend.app.jobs.scrape_legislation \
  --source asamblea --years 2026 --limit 10 --output data

# Reproducible selection of two records (source IDs, not decree numbers).
python -m backend.app.jobs.scrape_legislation \
  --source asamblea --document-ids 4530 6108 --output data

# Production destination: separate prefix in an existing bucket.
python -m backend.app.jobs.scrape_legislation \
  --source asamblea --years 2025 2026 \
  --bucket YOUR_CORPUS_BUCKET --prefix legislation

# Enumerate every year advertised by the source, explicitly opt in.
python -m backend.app.jobs.scrape_legislation \
  --source asamblea --all-years --bucket YOUR_CORPUS_BUCKET

# Diario Oficial pilot: one advertised month, two archive files, entirely local.
python -m backend.app.jobs.scrape_legislation \
  --source diario_oficial --years 2026 --months 10 --limit 2 --output data

# Diario Oficial: selected years, all available months, existing S3 bucket.
python -m backend.app.jobs.scrape_legislation \
  --source diario_oficial --years 2025 2026 --bucket YOUR_CORPUS_BUCKET

# Direct archive ID (not the printed Diario Oficial issue number).
python -m backend.app.jobs.scrape_legislation \
  --source diario_oficial --document-ids 31859 --output data
```

`S3_BUCKET` is supported as an alternative to `--bucket`. `--output` explicitly
selects local storage even if that environment variable is set. The collector
does not load `.env` automatically; export variables or pass CLI arguments.
It does not use or modify the API's `S3_FILES_PREFIX`/`S3_TEXT_PREFIX` settings.
`--limit` counts records considered, including records skipped on a resumed run;
remove it or increase it to continue beyond the pilot.

## Diario Oficial catalog and dates

The adapter reads advertised years from the archive home page. For each year it
queries `/api/v1/meses-disponibles` using a read-only form POST, then queries
`/api/v1/diarios-disponibles` with `year` and `month`. The returned `Id` identifies
the download at `/seleccion/{Id}`. IDs are deduplicated across the requested
catalogs. No browser, authentication or guessed numeric ID range is required.

`--months 1 2 ...` is an optional Diario-only filter on the months advertised for
each selected year. Without it, all advertised months are visited. An absent
requested month or an explicitly empty `data` array yields no records; unknown
years, malformed JSON and unexpected response shapes fail visibly. `--all-years`
explicitly opts into every year advertised by the archive, including historical
scans likely to need OCR. Catalog traversal uses descending years/months and
preserves the source's order within each month.

The source's `FechaInicio` is **not always an exact publication date**. In the
historical archive, `FechaInexacta=1` occurs with files such as
`1847_Parte19.pdf`. The adapter preserves the original row and catalog date,
sets `publication_date_precision: approximate`, and leaves `published_at` empty.
Only a parseable date explicitly flagged exact becomes `published_at`. Missing
or invalid dates/precision flags remain `unknown` rather than being invented.

A first-time direct ID download has no API row. Its download filename is retained;
a filename like `01-10-2026.pdf` can supply the storage year and `filename_date`,
but does not establish an exact `published_at`. Discover the record through its
year/month with `--refresh` to enrich that metadata. A later direct-ID refresh
reuses any catalog row already in its checkpoint, preserving discovered metadata.
To detect changes to API metadata itself, refresh through the catalog again.

Each Diario record has `document_type: official_gazette` and
`document_granularity: archive_file`. The catalog ID is not the printed issue
number. Printed issue numbers and volumes are not guessed from filenames.

## Storage contract

With the default prefix, the same hierarchy is created in the local destination
or the S3 bucket:

```text
legislation/asamblea/
  files/2021/asamblea-4530.PDF
  text/2021/asamblea-4530.txt
  pages/2021/asamblea-4530.json
  metadata/2021/asamblea-4530.json
  state/asamblea-4530.json
  versions/asamblea-4530/<revision>/
    original.PDF
    detail.html
    text.txt
    pages.json
    metadata.json
  runs/<run-id>.json
```

Diario uses the same hierarchy under `legislation/diario_oficial/`, for example
`files/2026/diario_oficial-31859.PDF` and
`text/2026/diario_oficial-31859.txt`. Its revision contains `detail.json` instead
of `detail.html`: a deterministic per-record snapshot of the catalog URL, query,
raw row and download filename. HTML snapshots for Asamblea remain unchanged.

Identifiers combine the source and its native record ID, **not** a title or decree
number. The storage year is fixed at the first publication, preferring issuance
date, publication date, then catalog year (`undated` if none is available).

Canonical PDF and TXT paths share the same relative stem. This matches the
existing S3 indexer's path convention, including uppercase `.PDF`. The future
legislation indexer should read completed state/manifests and their explicit
artifact keys; adapting the current `supreme_court` restriction is out of scope.
No search index is created or updated by this command.

Metadata schema version 1 includes:

- Stable `id`, `source_id`, source/detail URL and original URL; title and document
  type as advertised by the source; decree number, subject and publication data.
- Issuance/publication dates in ISO format when parseable, and the original
  `source_fields` so missing/unparseable data is not discarded.
- SHA-256 hashes of original bytes, source snapshot and extracted text;
  `extraction_policy`, schema version, page count and OCR candidate pages.
- Bucket (S3 only), explicit canonical `artifacts` and immutable
  `version_artifacts` object keys, including the configured S3 prefix.
- `legal_status: unverified`; a downloaded law is not assumed to be current.

Page JSON includes one-based page numbers, text, and `[start, end)` Python string
offsets into the complete UTF-8 text **after decoding**. Pages are joined with two
newlines. These boundaries allow later indexing by article/passage and citations
back to pages without losing the original document.

The revision fingerprint includes the PDF hash, source snapshot hash, parsed metadata,
schema and extractor policy/version. Revised source files or parser policies
create new revisions; previous revision artifacts are retained. Original bytes
are preserved exactly, including the extra bytes before `%PDF-` observed in some
Asamblea downloads. Normalization for extraction happens only in memory.

## Resume, refresh and incomplete documents

The source's `state/<id>.json` object is the completion marker. All required
objects must exist before a record is skipped. The collector writes `pending`
before work and publishes completed state **last**. Failures remain retryable;
rerun the same command after an interruption. Checkpoints live in the selected
destination, so S3 runs can resume on a replacement EC2 instance.

Use `--refresh` to re-fetch previously completed records and detect source changes:

```bash
python -m backend.app.jobs.scrape_legislation \
  --source asamblea --years 2025 2026 --bucket YOUR_CORPUS_BUCKET --refresh
```

When the revision is unchanged, canonical PDFs/text are not rewritten (preserving
their ETags). A metadata-only source change still creates a revision. Missing
artifacts trigger repair. Raw downloads and detail snapshots are archived before
extraction, including failed extractions where possible.

A page with fewer than `--min-page-characters` characters (default 20) makes the
document an OCR/review candidate: state `needs_ocr`, `indexable: false`. This is
a conservative heuristic; a genuinely blank page can also trigger it. The raw
PDF and partial text/pages remain in the immutable revision, but no canonical
TXT is published under `text/`. Extraction failures are marked `failed`, never
indexed as empty documents. OCR itself is not implemented in this first adapter.

Each run writes a JSON report and prints a summary. Exit codes: **0** completed
(possibly with OCR candidates), **1** document/discovery failure, **2** invalid
arguments, **130** interrupted. A completed limited run does not assert archive
completeness. Unexpected catalog layouts and response shapes fail visibly.
Some real Asamblea catalog entries have no PDF link (for example source record `7063`
on 2026-10-30). These are reported as retryable failures; they are not silently
treated as collected documents. Other records continue processing.

## Operating on EC2

Start with one worker, 2 vCPU and 4–8 GB RAM. Run it under a process supervisor
or `tmux`; downloads and extraction happen outside API startup. Use an instance
role through the standard boto3 credential chain, rather than embedded keys.
The role needs `s3:ListBucket` on the bucket (to distinguish missing objects from
denied access), and `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` for the chosen
corpus prefix. Delete is used only to remove a stale canonical text export when
a refreshed PDF needs OCR; immutable revision objects are never deleted.

Use **one writer per source and destination prefix**. Concurrent runs for the
same source/prefix are not supported. Different source adapters have isolated
subtrees. Keep checkpoints/manifests and revision history when configuring S3
lifecycle rules; deleting them defeats resume/history guarantees.

HTTP requests (GET and read-only catalog POST) default to at least 1.5 seconds
between starts per host. The client
checks `robots.txt`, respects crawl delays and `Retry-After`, retries transient
errors up to four attempts, and fails on access denial. Redirects must stay on
the source's HTTPS host allowlist. Responses are bounded to 50 MiB by default;
raise `--max-download-mb` for known larger files. Layout changes, retries and
failed URLs appear in logs. A sustained 403/challenge requires investigation;
the collector does not bypass it.

### Asamblea TLS chain

At verification time (2026-10-30), the Asamblea server sent only its leaf TLS
certificate, omitting the Sectigo OV R36 intermediate. OpenSSL-based clients
could not build the chain, although clients that fetch intermediates succeeded.
The adapter supplies the public intermediate in `app/ingestion/certs/`, combined
with Requests' normal root bundle in a temporary file. Certificate/hostname
verification stays enabled; no `verify=False` fallback is used. Standard Requests
CA environment overrides still apply if explicitly configured.

The intermediate was obtained from the issuer URL advertised in the leaf's AIA:
`http://crt.sectigo.com/SectigoPublicServerAuthenticationCAOVR36.crt`. Its signature
was verified against the normal trusted roots before inclusion. DER SHA-256:
`6542d176bed50f193c0ce297ae44ecd8a0a86bec2ede682769344059b4e78530`.
It expires on 2036-03-21. Revisit this bundled intermediate if the source changes
certificate issuers or starts serving a complete chain.

## Additional sources and validation

Shared HTTP, extraction, storage and pipeline modules live in `app/ingestion/`.
Add a source adapter implementing discovery, reference construction and fetching,
then register it in `app/jobs/scrape_legislation.py`. The judicial portal can be
added on the same branch without changing the storage contract. Adapters for HTML
or gazette-level segmentation may extend extraction
with an explicit schema/policy version.

Offline tests use observed Asamblea detail HTML, Diario API field shapes and
generated PDF fixtures, plus botocore's S3 Stubber. They cover parsing, discovery,
GET/POST retries, version history, resume/repair, date precision and OCR handling:

```bash
pip install pytest opensearch-py==3.0.0
python -m pytest backend/tests/ingestion -q
```

`opensearch-py` is needed by the repository's existing parent test configuration;
these tests make no OpenSearch connection. Live smoke tests should always use a
small explicit selection and a local or dedicated test destination.
