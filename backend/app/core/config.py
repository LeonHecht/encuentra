from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # read .env at project root, allow unknowns (or set to "forbid" if you list all fields)
    model_config = SettingsConfigDict(
        env_file=".env",
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
    OPENSEARCH_BULK_CHUNK_SIZE: int = 500
    OPENSEARCH_SIGV4: bool = False
    OPENSEARCH_USERNAME: str | None = None
    OPENSEARCH_PASSWORD: str | None = None
    OPENSEARCH_CA_CERT: str | None = None

    # --- OpenAI ---
    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str = "gpt-5-nano"
    MAX_DOC_TOKENS: int = 2000
    MAX_DOCS: int = 3

settings = Settings()
