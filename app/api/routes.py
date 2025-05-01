from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from datetime import datetime

router = APIRouter()

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["csv", "json", "pdf"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Ruta donde se guarda el archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"bronze/{timestamp}_{file.filename}"

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": "File uploaded", "path": save_path}
