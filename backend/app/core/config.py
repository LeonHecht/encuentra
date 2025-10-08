from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "local"
    API_VERSION: str = "v1"
    PORT: int = 8000
    ALLOWED_ORIGINS: str ="http://localhost:5173"
    CORPUS_PATH: str = "data/static_corpus"
    DATA_UPLOAD: str = "backend/app/api/data/user_uploads"

    # Search backend configuration
    SEARCH_BACKEND: str = "opensearch"  # bm25 | opensearch
    OPENSEARCH_HOSTS: str = "http://localhost:9200"
    OPENSEARCH_INDEX_PREFIX: str = "encuentra"
    OPENSEARCH_USERNAME: str | None = None
    OPENSEARCH_PASSWORD: str | None = None
    OPENSEARCH_VERIFY_CERTS: bool = True
    OPENSEARCH_CA_CERT: str | None = None
    OPENSEARCH_TIMEOUT: int = 30
    OPENSEARCH_BULK_CHUNK_SIZE: int = 500

    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str = "gpt-5-nano"
    MAX_DOC_TOKENS: int = 2000
    MAX_DOCS: int = 3

    model_config = ConfigDict(
        env_file=".env",
        # keep forbidding unknowns (safer) now that we’ve added the fields
        extra="forbid",
    )

settings = Settings()
