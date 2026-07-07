import re
from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\-\s()]{6,30}$")


def validate_phone(phone: str) -> str:
    normalized = phone.strip()
    if not PHONE_PATTERN.match(normalized):
        raise HTTPException(status_code=422, detail="Enter a valid phone number.")
    return normalized


async def validate_upload(file: UploadFile, max_upload_mb: int) -> bytes:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, and PNG images are supported.")

    max_bytes = max_upload_mb * 1024 * 1024
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Image must be {max_upload_mb}MB or smaller.")
    return data
