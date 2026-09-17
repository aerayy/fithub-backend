# app/api/config.py — kimlik doğrulaması gerektirmeyen uygulama yapılandırması
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.services.app_settings import public_config

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/app")
def get_app_config(db=Depends(get_db)):
    """Uygulama açılışında (giriş öncesi dahil) okunur: özellik bayrakları + AI koç adı/deneme süresi."""
    return public_config(db)
