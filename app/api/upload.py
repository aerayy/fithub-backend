"""
Image upload endpoint using Cloudinary.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from app.core.security import get_current_user
from app.core.config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
import cloudinary
import cloudinary.uploader

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)


ALLOWED_FOLDERS = {
    "chat": "fithub/chat",
    "profile": "fithub/profile-photos",
    "meal": "fithub/meal-photos",
    "body-form": "fithub/body-form",
}


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Query("chat", description="Target folder: chat, profile, meal, body-form"),
    current_user=Depends(get_current_user),
):
    """Upload an image to Cloudinary. Returns URL and metadata."""
    if not CLOUDINARY_CLOUD_NAME:
        raise HTTPException(status_code=500, detail="Cloudinary not configured")

    cloud_folder = ALLOWED_FOLDERS.get(folder, "fithub/chat")

    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Use JPEG, PNG, WebP or GIF.",
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder=cloud_folder,
            resource_type="image",
            transformation=[
                {"width": 1200, "height": 1200, "crop": "limit"},
                {"quality": "auto", "fetch_format": "auto"},
            ],
        )
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "width": result.get("width"),
            "height": result.get("height"),
            "size_bytes": len(contents),
            "format": result.get("format"),
        }
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise HTTPException(status_code=500, detail="Image upload failed")
