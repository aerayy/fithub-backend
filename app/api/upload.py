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
    "chat-voice": "fithub/chat-voice",
    "profile": "fithub/profile-photos",
    "meal": "fithub/meal-photos",
    "body-form": "fithub/body-form",
    "exercise-video": "fithub/exercise-videos",
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


@router.post("/video")
async def upload_video(
    file: UploadFile = File(...),
    folder: str = Query("exercise-video"),
    current_user=Depends(get_current_user),
):
    """
    Video upload — eager H.264 transcode upload anında yapılır.
    Bu, Android cihazlarda HEVC oynama sorununu önler ve cold transcode delay
    yaratmaz (varyant Cloudinary storage'a kalıcı eklenir).
    """
    if not CLOUDINARY_CLOUD_NAME:
        raise HTTPException(status_code=500, detail="Cloudinary not configured")

    cloud_folder = ALLOWED_FOLDERS.get(folder, "fithub/exercise-videos")

    allowed_types = ["video/mp4", "video/quicktime", "video/webm", "video/x-matroska"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Video tipi desteklenmiyor: {file.content_type}",
        )

    contents = await file.read()
    if len(contents) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Video çok büyük (max 100MB)")

    try:
        # Eager: upload anında H.264 varyantı kalıcı olarak üretilir.
        # eager_async=True — büyük dosyalarda timeout olmasın diye.
        result = cloudinary.uploader.upload(
            contents,
            folder=cloud_folder,
            resource_type="video",
            eager=[
                {"format": "mp4", "video_codec": "h264", "quality": "auto"},
            ],
            eager_async=True,
        )
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "duration": result.get("duration"),
            "width": result.get("width"),
            "height": result.get("height"),
            "size_bytes": len(contents),
            "format": result.get("format"),
            "eager": result.get("eager", []),
        }
    except Exception as e:
        logger.error(f"Cloudinary video upload failed: {e}")
        raise HTTPException(status_code=500, detail="Video yükleme başarısız")


@router.post("/voice")
async def upload_voice(
    file: UploadFile = File(...),
    duration_sec: int = Query(0, description="Audio duration in seconds"),
    current_user=Depends(get_current_user),
):
    """Sesli mesaj upload (chat icin). Cloudinary 'video' resource type kullanir
    cunku ses dosyalari da bu kategoride yonetilir.

    Frontend kayit formati: m4a (iOS) veya AAC (Android). Cloudinary
    desteklediginden direkt upload eder.
    """
    if not CLOUDINARY_CLOUD_NAME:
        raise HTTPException(status_code=500, detail="Cloudinary not configured")

    cloud_folder = ALLOWED_FOLDERS["chat-voice"]

    allowed_types = ["audio/mp4", "audio/m4a", "audio/aac", "audio/mpeg", "audio/wav", "audio/ogg", "audio/webm", "video/mp4"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Audio tipi desteklenmiyor: {file.content_type}",
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB max for voice (~10 min @ 128kbps)
        raise HTTPException(status_code=400, detail="Sesli mesaj cok buyuk (max 10MB)")

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder=cloud_folder,
            resource_type="video",  # Cloudinary'de audio = video resource type
        )
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "duration_sec": int(result.get("duration") or duration_sec or 0),
            "size_bytes": len(contents),
            "format": result.get("format"),
        }
    except Exception as e:
        logger.error(f"Cloudinary voice upload failed: {e}")
        raise HTTPException(status_code=500, detail="Sesli mesaj yuklenemedi")
