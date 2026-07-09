"""AI Coach subscription endpoints (Starter/Pro/Elite).

Endpoints:
  GET  /ai-coach/subscription           — current tier + quotas
  POST /ai-coach/subscription/mock      — mock purchase (dev/test)
  POST /ai-coach/subscription/cancel    — cancel active subscription

Apple IAP receipt validation endpoint will land here post-DUNS.
"""
import logging
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user
from app.core.database import get_db
from app.services import ai_subscription_service as ai_sub
from app.services import revenuecat_service as rc

router = APIRouter(prefix="/ai-coach", tags=["ai-coach"])
logger = logging.getLogger(__name__)

# GÜVENLİK (LAUNCH_AUDIT.md B1): mock purchase SADECE dev/test için.
# Prod'da bu env flag set edilmez → endpoint 403 döner, kimse bedava tier alamaz.
# Gerçek satın alma RevenueCat receipt validation ile gelecek.
_ALLOW_MOCK_PURCHASE = os.getenv("ALLOW_MOCK_PURCHASE", "").strip().lower() in ("1", "true", "yes")


class MockSubscribeRequest(BaseModel):
    tier: str           # 'starter' | 'pro' | 'elite'
    billing_period: str = "monthly"  # 'monthly' | 'yearly'


@router.get("/subscription")
def get_subscription(user=Depends(get_current_user), db=Depends(get_db)):
    """Returns full subscription + quota usage status."""
    try:
        status = ai_sub.get_subscription_status(db, user["id"])
        return status
    except Exception as e:
        logger.exception("get_subscription failed user=%s", user.get("id"))
        raise HTTPException(status_code=500, detail="Abonelik durumu alınamadı. Lütfen tekrar dene.")


@router.post("/subscription/mock")
def mock_subscribe(
    req: MockSubscribeRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Dev/test mock purchase. Apple IAP DUNS sonrasi gercek receipt validation
    eklenecek; bu endpoint sadece development testleri icin.

    Returns 201-like dict with the created subscription.
    """
    # GÜVENLİK: prod'da ALLOW_MOCK_PURCHASE set değil → kimse bedava tier alamaz.
    if not _ALLOW_MOCK_PURCHASE:
        logger.warning("mock_subscribe blocked (prod) user=%s", user.get("id"))
        raise HTTPException(status_code=403, detail="Mock purchase is disabled")
    try:
        result = ai_sub.create_mock_subscription(
            db, user["id"], req.tier, req.billing_period
        )
        return {"ok": True, "subscription": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("mock_subscribe failed user=%s", user.get("id"))
        raise HTTPException(status_code=500, detail="Abonelik başlatılamadı. Lütfen tekrar dene.")


@router.post("/subscription/sync")
def sync_subscription(user=Depends(get_current_user), db=Depends(get_db)):
    """RevenueCat ile anlık senkron — uygulama satın alma HEMEN sonrasında
    (ve foreground'a dönünce) çağırır. Webhook'un gelmesini beklemeden,
    RevenueCat REST API'sinden abonenin güncel entitlement'ını okuyup
    ai_subscriptions'ı günceller ve tam durum döner.

    RevenueCat yapılandırılmamışsa (secret key yok) 503 döner — uygulama
    bunu 'henüz canlı değil' olarak ele alır.
    """
    if not os.getenv("REVENUECAT_SECRET_API_KEY", "").strip():
        raise HTTPException(status_code=503, detail="RevenueCat not configured")
    try:
        subscriber = rc.fetch_subscriber(str(user["id"]))
        rc.sync_from_subscriber(db, user["id"], subscriber)
        return ai_sub.get_subscription_status(db, user["id"])
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("sync_subscription failed user=%s", user.get("id"))
        raise HTTPException(status_code=502, detail="Abonelik senkronu başarısız. Lütfen tekrar dene.")


@router.post("/subscription/cancel")
def cancel_subscription(user=Depends(get_current_user), db=Depends(get_db)):
    """Cancel the user's active AI Coach subscription."""
    try:
        canceled = ai_sub.cancel_subscription(db, user["id"])
        return {"ok": True, "canceled": canceled}
    except Exception as e:
        logger.exception("cancel_subscription failed user=%s", user.get("id"))
        raise HTTPException(status_code=500, detail="İptal işlemi başarısız. Lütfen tekrar dene.")
