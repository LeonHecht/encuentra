from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid
from app.services.bm25 import bm25_engine
from app.core.config import settings

router = APIRouter()


@router.post("/upload", summary="Upload a document into a space")
async def upload_file(file: UploadFile = File(...), space: str = "default"):
    # sanitize/validate space name
    space_dir = Path(settings.DATA_UPLOAD) / space
    space_dir.mkdir(exist_ok=True)
    # generate a unique filename
    file_id = uuid.uuid4().hex
    ext = Path(file.filename).suffix
    dest = space_dir / f"{file_id}{ext}"
    try:
        contents = await file.read()
        dest.write_bytes(contents)
    except Exception as e:
        raise HTTPException(500, f"Error saving file: {e}")
    bm25_engine.index(space) 
    return {"space": space, "file_id": file_id, "filename": file.filename}
