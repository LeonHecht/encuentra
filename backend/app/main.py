from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .core.config import settings
from .api.v1.endpoints import search
from app.services.bm25 import bm25_engine
from .api.v1.endpoints import files
from app.api.v1.endpoints import chat
from app.api.v1.endpoints import auth
from app.services import auth as auth_service


app = FastAPI(
    title="Encuentra API",
    version=settings.API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),  # or ["*"] for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix=f"/{settings.API_VERSION}")
app.include_router(files.router, prefix=f"/{settings.API_VERSION}")
app.include_router(chat.router, prefix=f"/{settings.API_VERSION}")
app.include_router(auth.router, prefix=f"/{settings.API_VERSION}")
app.mount("/downloads", StaticFiles(directory="backend/app/static/downloads"), name="downloads")

@app.get("/ping")
def ping():
    return {"satus": "pong"}

# indexamos una sola vez al startup
@app.on_event("startup")
def on_startup():
    auth_service.init_data()
    bm25_engine.index(space="supreme_court")
    uploads_root = Path(settings.DATA_UPLOAD)
    if uploads_root.exists():
        for path in uploads_root.glob("*/*"):
            if path.is_dir():
                rel = path.relative_to(uploads_root)
                bm25_engine.index(space=str(rel))
