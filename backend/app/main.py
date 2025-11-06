from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .core.config import settings
from .api.v1.endpoints import search
from .services.search import search_engine
from .api.v1.endpoints import files
from .api.v1.endpoints import chat
from .api.v1.endpoints import auth
from .api.v1.endpoints import billing
from .api.v1.endpoints import billing


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
app.include_router(billing.router, prefix=f"/{settings.API_VERSION}")
app.include_router(billing.router, prefix=f"/{settings.API_VERSION}")

static_dir = Path(__file__).resolve().parent / "static" / "downloads"
app.mount("/downloads", StaticFiles(directory=static_dir), name="downloads")

@app.get("/ping")
def ping():
    return {"status": "pong"}

# indexamos una sola vez al startup
@app.on_event("startup")
def on_startup():
    search_engine.index(space="supreme_court")
    uploads_root = Path(settings.DATA_UPLOAD)
    if uploads_root.exists():
        for path in uploads_root.glob("*/*"):
            if path.is_dir():
                rel = path.relative_to(uploads_root)
                search_engine.index(space=str(rel))
