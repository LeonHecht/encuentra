import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Read env from an environment-specific file first (if present), then fallback to .env
    # Set APP_ENV=production (or staging, etc.) to load .env.production before .env
    _env = os.getenv("APP_ENV", "local")
    model_config = SettingsConfigDict(
        env_file=(f".env.{_env}", ".env"),
        case_sensitive=False,
        extra="ignore",   # or "forbid" IF you list every possible env var here
    )

    # --- Core ---
    CORPUS_PATH: str = "./data/static_corpus"
    SEARCH_BACKEND: str = "bm25"

    APP_ENV: str = "local"
    API_VERSION: str = "v1"
    PORT: int = 8000
    ALLOWED_ORIGINS: str ="http://localhost:5173"
    CORPUS_PATH: str = "data/static_corpus"
    DATA_UPLOAD: str = "backend/app/api/data/user_uploads"

    # Search backend configuration
    SEARCH_BACKEND: str = "opensearch"  # bm25 | opensearch
    OPENSEARCH_HOSTS: str = "http://localhost:9200"
    OPENSEARCH_TIMEOUT: int = 30
    OPENSEARCH_VERIFY_CERTS: bool = False
    OPENSEARCH_INDEX_PREFIX: str = "encuentra"
    OPENSEARCH_BULK_CHUNK_SIZE: int = 500   # Send 500 documents per HTTP request to _bulk
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

    # --- S3 corpus/files (optional; used in staging/prod) ---
    # Bucket that holds corpus.jsonl and the original files
    S3_BUCKET: str | None = None
    # Object key for the corpus JSONL, e.g. "staging/corpus.jsonl" or "prod/corpus.jsonl"
    S3_CORPUS_KEY: str | None = None
    # Prefix for original files within the bucket, e.g. "staging/files/" or "prod/files/"
    S3_FILES_PREFIX: str | None = None
    # TTL in seconds for presigned URLs to original files
    S3_URL_TTL: int = 7 * 24 * 60 * 60  # default 7 days
    # Whether to generate S3 presigned URLs during indexing (expensive for large corpora)
    S3_PRESIGN_ON_INDEX: bool = False
    # Whether to generate S3 presigned URLs at query time (recommended)
    S3_PRESIGN_ON_QUERY: bool = True

    # --- Indexing controls ---
    # If true, force a rebuild of indexes on startup (expensive for OpenSearch in staging/prod)
    FORCE_REINDEX_ON_STARTUP: bool = False
    # If true, skip rebuilding on startup unless the space is missing (recommended for staging/prod)
    SKIP_REINDEX_ON_STARTUP: bool = True

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
