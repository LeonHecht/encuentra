## Backend search backends

The API can run either entirely in memory using the bundled BM25 index or
delegate search to an external OpenSearch cluster. The backend is selected via
the `SEARCH_BACKEND` environment variable (`bm25` by default).

### Using the in-memory BM25 engine (default)

No additional setup is required; the application will load
`data/static_corpus/corpus.jsonl` at startup and keep all indexes in memory. The
same code path is still used by the test suite.

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
the host changes.

1. Run OpenSearch on the EC2 instance. Example single-node container:

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
