from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.v1.endpoints import search
from app.services.bm25 import bm25_engine
from .api.v1.endpoints import files
from app.api.v1.endpoints import chat


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

@app.get("/ping")
def ping():
    return {"satus": "pong"}

# indexamos una sola vez al startup
@app.on_event("startup")
def on_startup():
    bm25_engine.index(space="supreme_court")