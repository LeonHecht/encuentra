from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "local"
    API_VERSION: str = "v1"
    PORT: int = 8000
    ALLOWED_ORIGINS: str = ""
    CORPUS_PATH: str = "data/static_corpus"
    DATA_UPLOAD: str = "backend/app/api/data/user_uploads"

    class Config:
        env_file = ".env"

settings = Settings()
