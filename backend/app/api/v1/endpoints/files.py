from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from pathlib import Path
from typing import List
import uuid

from app.services.bm25 import bm25_engine
from app.core.config import settings
from app.dependencies import get_current_user
from app.services.auth import get_accessible_spaces, UserData

router = APIRouter()

# Base folder for uploads
UPLOADS_ROOT = Path(settings.DATA_UPLOAD)
UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)

@router.post("/upload", summary="Upload one or multiple documents into a space")
async def upload_file(
    files: List[UploadFile] = File(...),
    space: str = Form("default"),
    user: UserData = Depends(get_current_user),
):
    """
    files: list of UploadFile
    space: the name of the space (folder) under UPLOADS_ROOT
    """
    if space not in get_accessible_spaces(user.username):
        raise HTTPException(403, detail="Space not accessible")
    space_dir = UPLOADS_ROOT / space
    space_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for file in files:
        # Unique file ID + preserve extension
        file_id = uuid.uuid4().hex
        ext = Path(file.filename).suffix
        dest = space_dir / f"{file_id}{ext}"
        try:
            contents = await file.read()
            dest.write_bytes(contents)
        except Exception as e:
            raise HTTPException(500, f"Error saving {file.filename}: {e}")

        saved.append({
            "file_id": file_id,
            "filename": file.filename,
            "saved_path": dest.name,
        })

    # Rebuild index for this space so the new docs are searchable
    bm25_engine.index(space)

    return {
        "space": space,
        "uploaded": saved,
    }
