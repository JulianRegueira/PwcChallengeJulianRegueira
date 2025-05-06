from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
import os
import shutil

router = APIRouter(
    prefix="/upload",
    tags=["upload"]
)

@router.post("/", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV/JSON/PDF file into the Bronze layer.
    """
    # Validate extension
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("csv", "json", "pdf"):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Ensure bronze folder exists
    os.makedirs("bronze", exist_ok=True)

    # Timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"bronze/{timestamp}_{file.filename}"

    # Write file to disk
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": "File uploaded successfully", "path": save_path}
