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

    # --- OpenAI ---
    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str = "gpt-5-nano"
    MAX_DOC_TOKENS: int = 2000
    MAX_DOCS: int = 3

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
