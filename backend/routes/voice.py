import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "voice_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-voice")
async def upload_voice(file: UploadFile = File(...)):
    filename = f"{datetime.utcnow().timestamp()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"message": "Uploaded successfully", "filename": filename}
