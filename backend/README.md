## Backend search backends

The API can run either entirely in memory using the bundled BM25 index or
delegate search to an external OpenSearch cluster. The backend is selected via
the `SEARCH_BACKEND` environment variable (`opensearch` by default in this repo).

### Using the in-memory BM25 engine

No additional setup is required; the application will load
`data/static_corpus/corpus.jsonl` at startup and keep all indexes in memory. The
same code path is still used by parts of the test suite. Set
`SEARCH_BACKEND=bm25` to use this mode.

### Using OpenSearch

1. **Install OpenSearch and create credentials.** Provision an OpenSearch
   domain (self-hosted or managed). Create a user that has permissions to
   create/delete indexes and run bulk indexing operations.
2. **Set environment variables** (e.g. in `.env`):
   ```env
   SEARCH_BACKEND=opensearch
   OPENSEARCH_HOSTS=https://your-cluster.example.com:9200
   OPENSEARCH_USERNAME=your-user
   OPENSEARCH_PASSWORD=your-password
   # optional, but recommended when using HTTPS
   OPENSEARCH_CA_CERT=/path/to/ca.pem
   OPENSEARCH_INDEX_PREFIX=encuentra
   ```
3. **Start the API**. On startup the FastAPI app will synchronise the
   filesystem corpus with OpenSearch by re-creating per-space indexes and
   loading documents through the bulk API.
4. **Uploading new files.** Whenever a user uploads documents the API calls the
   selected backend's `index()` method; for OpenSearch this translates into a
   fresh bulk import for that space.

The OpenSearch backend currently stores documents with a Spanish analyser and
expects the same filesystem layout used by the BM25 implementation. This keeps
feature parity between both modes, enabling a gradual migration to a scalable
search cluster while retaining the local developer experience.

### OpenSearch in Docker on EC2

Staging/prod can point at a normal OpenSearch node running in Docker on an EC2
instance. This uses the same non-SigV4 client path as local development; only
the host changes. The reusable files live in `../infra/ec2-opensearch`.

1. Run OpenSearch on the EC2 instance. You can use
   `../infra/ec2-opensearch/user-data.sh` as EC2 user data, or copy
   `../infra/ec2-opensearch/docker-compose.yml` to the instance and run
   `docker compose up -d`. Equivalent single-container command:

   ```bash
   docker run -d --name encuentra-opensearch \
     -p 9200:9200 -p 9600:9600 \
     -e discovery.type=single-node \
     -e plugins.security.disabled=true \
     -e OPENSEARCH_JAVA_OPTS="-Xms1g -Xmx1g" \
     opensearchproject/opensearch:3
   ```

2. Configure the API environment to use that EC2-hosted node:

   ```env
   SEARCH_BACKEND=opensearch
   OPENSEARCH_HOSTS=http://<ec2-private-ip-or-dns>:9200
   OPENSEARCH_SIGV4=false
   OPENSEARCH_VERIFY_CERTS=false
   OPENSEARCH_INDEX_PREFIX=encuentra-stg
   SKIP_REINDEX_ON_STARTUP=true
   FORCE_REINDEX_ON_STARTUP=false
   ```

3. Networking: if the API also runs in AWS, prefer the EC2 private IP/private
   DNS and allow inbound TCP 9200 only from the API security group. Avoid
   exposing 9200 publicly unless it is protected by a firewall, VPN, or reverse
   proxy with authentication/TLS.
4. Local dev remains unchanged. Use Docker OpenSearch with:
   ```env
   SEARCH_BACKEND=opensearch
   OPENSEARCH_HOSTS=http://localhost:9200
   OPENSEARCH_SIGV4=false
   OPENSEARCH_VERIFY_CERTS=false
   ```

AWS-managed OpenSearch remains available only when explicitly enabled:

```env
OPENSEARCH_SIGV4=true
OPENSEARCH_AWS_REGION=us-east-2
OPENSEARCH_AWS_SERVICE=aoss
OPENSEARCH_HOSTS=https://<collection-id>.<region>.aoss.amazonaws.com
OPENSEARCH_VERIFY_CERTS=true
```

## Supreme Court citations

The case retrieval service searches the existing `supreme_court` OpenSearch
index. A search result and the corresponding decision excerpt share a
permalink at `/cases/supreme-court?id=<case-id>`.

For local testing, set `CASE_CITATION_BASE_URL=http://localhost:8000` to enable
the citation page. Use the public HTTPS API origin as the value in any
environment that should serve these pages. With the setting unset, the page
is disabled. Enabling it allows anyone with a case URL to read the indexed
Supreme Court excerpt. The citation URL does not depend on an S3 download.

## Local MCP testing

From the repository root, run the API against a local OpenSearch index:

```bash
MCP_ENABLED=true CASE_CITATION_BASE_URL=http://127.0.0.1:8000 \
  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Connect MCP Inspector over Streamable HTTP at `http://127.0.0.1:8000/mcp`.
Call `search` with a query and pass a result ID to `fetch`. Both tools return
the same citation URL. Fetch and the citation page show up to 64,000
characters of indexed text. Fetch sets `metadata.truncated` when the decision
is longer.

## Public MCP access and usage

The endpoint is disabled by default. To enable anonymous access, apply the
Supabase search-log migration and set `MCP_ENABLED=true` and
`CASE_CITATION_BASE_URL` to the API origin. The SDK validates the request host
and any Origin header against that configured origin. Use the public HTTPS
origin when connecting a remote MCP client.

Set `MCP_TOOL_CALLS_PER_MINUTE` (default 120) and
`MCP_MAX_CONCURRENT_TOOL_CALLS` (default 4) to set the shared limits for
`search` and `fetch`. The limits are enforced in the FastAPI process. The
current backend image runs a single worker.

Successful MCP searches, including searches with zero results, are written to
`search_query_logs` using the backend-only Supabase service-role
`SUPABASE_KEY`. These rows contain the query, result count, and
`metadata.source = 'mcp'`, with a null `user_id`. Fetches are excluded from the
search log. Website searches continue to use their existing user IDs and
policies. A logging failure does not prevent the search results from being
returned.

```sql
select date_trunc('day', created_at) as day,
       case when user_id is null then 'mcp' else 'website' end as source,
       count(*) as searches
from public.search_query_logs
group by 1, 2
order by 1 desc, 2;
```

## Environments and .env files

This backend supports environment-specific configuration files using `APP_ENV`:

- Set the process environment variable `APP_ENV` to one of: `local` (default), `staging`, `production`.
- At startup, settings are loaded from `.env` first, then `.env.{APP_ENV}` overrides matching keys if present.

Important: Because `APP_ENV` is read before any `.env` files are parsed, you must set `APP_ENV` in the real process environment (systemd, Docker, ECS, etc.), not inside `.env`.

### Recommended files at repo root

- `.env` (for local dev)
- `.env.staging`
- `.env.production`

Example contents for staging/prod when using S3 + self-hosted OpenSearch:

```env
# Backend selection
SEARCH_BACKEND=opensearch

# S3 corpus and files
S3_BUCKET=encuentra-data
S3_CORPUS_KEY=staging/corpus.jsonl   # or prod/corpus.jsonl
S3_FILES_PREFIX=staging/files/       # or prod/files/
S3_URL_TTL=604800                    # 7 days for presigned URLs

# OpenSearch Docker container on EC2
OPENSEARCH_HOSTS=http://<EC2-private-ip>:9200
OPENSEARCH_SIGV4=false
OPENSEARCH_USERNAME=encu_app
OPENSEARCH_PASSWORD=AppUserPwd_!234
OPENSEARCH_VERIFY_CERTS=false
# OPENSEARCH_INDEX_PREFIX=encuentra-stg  # optional: avoid collisions if sharing a cluster
```

For local development, keep your current setup (e.g. OpenSearch in Docker):

```env
# .env
SEARCH_BACKEND=opensearch
OPENSEARCH_HOSTS=http://localhost:9200
OPENSEARCH_SIGV4=false
ALLOWED_ORIGINS=http://localhost:5173
```

Use `FORCE_REINDEX_ON_STARTUP=true` for a one-time rebuild. Switch it back to
`false` afterward to avoid rebuilding the OpenSearch index on every deploy.
