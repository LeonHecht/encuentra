import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Read base .env first, then let an environment-specific file override it.
    # Set APP_ENV=production (or staging, etc.) to load .env.production after .env.
    _env = os.getenv("APP_ENV", "local")
    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{_env}"),
        case_sensitive=False,
        extra="ignore",   # or "forbid" IF you list every possible env var here
    )

    # --- Core ---
    APP_ENV: str = "local"
    API_VERSION: str = "v1"
    PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    CORPUS_PATH: str = "data/static_corpus"
    DATA_UPLOAD: str = "backend/app/api/data/user_uploads"

    # Search backend configuration
    SEARCH_BACKEND: str = "opensearch"  # opensearch | bm25
    OPENSEARCH_HOSTS: str = "http://localhost:9200"
    OPENSEARCH_TIMEOUT: int = 30
    OPENSEARCH_VERIFY_CERTS: bool = False
    OPENSEARCH_INDEX_PREFIX: str = "encuentra"
    OPENSEARCH_BULK_CHUNK_SIZE: int = 500   # Send 500 documents per HTTP request to _bulk
    OPENSEARCH_SEARCH_TIMEOUT: int = 10
    OPENSEARCH_ENABLE_HIGHLIGHTS: bool = True
    OPENSEARCH_HIGHLIGHT_FRAGMENT_SIZE: int = 200
    OPENSEARCH_SIGV4: bool = False
    OPENSEARCH_USERNAME: str | None = None
    OPENSEARCH_PASSWORD: str | None = None
    OPENSEARCH_CA_CERT: str | None = None
    OPENSEARCH_AWS_REGION: str | None = None
    OPENSEARCH_AWS_SERVICE: str = "aoss"  # "es" default, "aoss" for serverless

    # --- OpenAI ---
    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str = "gpt-5-nano"   # fall back to gpt-5-nano (will be overwritten by .env.[stage] files)
    MAX_DOC_TOKENS: int = 2000
    MAX_DOCS: int = 3
    CASE_METADATA_AUTO_ENRICH: bool = True
    CASE_METADATA_MODEL: str = "gpt-5-nano"
    CASE_METADATA_REASONING_EFFORT: str = "none"  # none | low | medium | high | xhigh
    CASE_METADATA_MAX_RETRIES: int = 2
    CASE_METADATA_PENDING_RETRY_MINUTES: int = 10


    # --- S3 corpus/files (optional; used in staging/prod) ---
    # Bucket that holds corpus.jsonl and the original files
    S3_BUCKET: str | None = None
    # Object key for the corpus JSONL, e.g. "staging/corpus.jsonl" or "prod/corpus.jsonl"
    # (legacy; optional if you index directly from S3 text files instead)
    S3_CORPUS_KEY: str | None = None
    # Prefix for original files (PDFs, etc.) within the bucket, e.g. "staging/files/" or "prod/files/"
    S3_FILES_PREFIX: str | None = None
    # Prefix for plain-text documents within the bucket, e.g. "staging/txt/" or "pdfs/text/txt/"
    # When set (along with S3_BUCKET), the OpenSearch indexer will prefer reading .txt files
    # from this prefix instead of relying on a corpus.jsonl file.
    S3_TEXT_PREFIX: str | None = None
    # TTL in seconds for presigned URLs to original files
    S3_URL_TTL: int = 7 * 24 * 60 * 60  # default 7 days
    # Whether to generate S3 presigned URLs during indexing (expensive for large corpora)
    S3_PRESIGN_ON_INDEX: bool = False
    # Whether search results should include presigned file URLs. This is cheap
    # when documents have s3_file_key populated by the incremental indexer.
    S3_PRESIGN_ON_SEARCH: bool = True
    # Whether to generate S3 presigned URLs at query time (recommended)
    S3_PRESIGN_ON_QUERY: bool = True

    # --- Indexing controls ---
    # If false, the web API never indexes during FastAPI startup. Use the
    # dedicated indexing job for large corpora in staging/prod.
    INDEX_ON_STARTUP: bool = False
    # If true, force a rebuild of indexes on startup (expensive for OpenSearch in staging/prod)
    FORCE_REINDEX_ON_STARTUP: bool = False
    # If true, skip rebuilding on startup unless the space is missing (recommended for staging/prod)
    SKIP_REINDEX_ON_STARTUP: bool = True
    # If true, incremental indexing deletes OpenSearch docs whose S3 text keys
    # no longer exist. Keep false until you are confident the S3 prefix is correct.
    OPENSEARCH_DELETE_MISSING_S3_DOCS: bool = False

    # --- Supabase ---
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None  # Service role key for backend (anon or service_role)
    SUPABASE_JWKS_URL: str | None = None  # For verifying JWT tokens with new ECC keys
    SUPABASE_JWT_SECRET: str | None = None  # Legacy HS256 shared secret

    # --- Stripe (optional) ---
    STRIPE_SECRET_KEY: str | None = None
    BILLING_RETURN_URL: str | None = None  # e.g. http://localhost:5173/settings/billing
    FRONTEND_BASE_URL: str | None = None   # Fallback for return URLs

settings = Settings()
