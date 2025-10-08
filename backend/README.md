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
