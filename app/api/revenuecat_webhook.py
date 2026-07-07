"""RevenueCat webhook endpoint.

RevenueCat, satın alma yaşam döngüsü olaylarını (INITIAL_PURCHASE, RENEWAL,
CANCELLATION, EXPIRATION, ...) buraya POST eder. Yenileme/iptal/süre bitişleri
sunucu-otoriter olarak buradan gelir; uygulama açık olmasa bile abonelik
durumu güncel kalır.

Güvenlik: RevenueCat dashboard'da webhook'a bir Authorization header değeri
tanımlanır (REVENUECAT_WEBHOOK_AUTH ile aynı). Bu header eşleşmezse istek
reddedilir — böylece kimse sahte "satın alındı" event'i gönderip bedava tier
alamaz.

Status kodu stratejisi:
  200 → işlendi VEYA kalıcı olarak atlandı (bilinmeyen product, anonim user).
        RC retry YAPMAZ.
  401 → auth başarısız.
  500 → geçici (DB) hata. RC saatler boyunca RETRY eder → event kaybolmaz.
"""
import hmac
import logging
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.core.database import get_db
from app.services import revenuecat_service as rc

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/revenuecat")
async def revenuecat_webhook(
    request: Request,
    authorization: str = Header(default=""),
    db=Depends(get_db),
):
    expected = os.getenv("REVENUECAT_WEBHOOK_AUTH", "").strip()
    if not expected:
        # Prod'da bu set edilmezse webhook'u AÇMIYORUZ — auth'suz işlem yok.
        logger.error("revenuecat webhook called but REVENUECAT_WEBHOOK_AUTH not configured")
        raise HTTPException(status_code=503, detail="webhook not configured")

    if not hmac.compare_digest((authorization or "").strip(), expected):
        logger.warning("revenuecat webhook auth mismatch")
        raise HTTPException(status_code=401, detail="unauthorized")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json body")

    event = (payload or {}).get("event") or {}
    etype = event.get("type", "?")

    try:
        result = rc.handle_webhook_event(db, event)
    except Exception:
        # Geçici/beklenmeyen hata → 500 → RevenueCat retry eder (event kaybolmaz).
        logger.exception("revenuecat webhook processing failed type=%s", etype)
        raise HTTPException(status_code=500, detail="processing error")

    logger.info("revenuecat webhook handled type=%s -> %s", etype, result)
    return {"ok": True, "result": result}
