"""
Home bundle endpoint — Flutter home ekrani icin tek istek, tum data.

Onceden Flutter 6+ ardisik istek yapiyordu (me, state, coaches, daily-targets,
workouts/active, notifications, water-intake/today). Her biri ~300ms latency.
Bu endpoint hepsini tek transaction'da DB'den cekip tek payload doner.

Dahil edilenler (tumu hizli DB sorgulari):
  - me           — client profili + onboarding durumu
  - state        — subscription + program state
  - coaches      — koc listesi
  - daily_targets — gunluk hedefler (kcal, su, adim)
  - workout      — aktif antrenman programi (gunluk)
  - notifications — son bildirimler
  - water_today  — bugunku su sayaci

Dahil edilmeyenler (yavas, OpenAI cache miss riski):
  - daily-motivation, recovery-tips, weekly-challenge — Flutter ayri lazy cagirir.
"""
import logging
from fastapi import Depends, HTTPException

from app.core.database import get_db
from app.core.security import require_role
from .routes import router

logger = logging.getLogger(__name__)


@router.get("/home-bundle")
def get_home_bundle(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Tum home ekrani icin tek istek. Her bir parca individual endpoint'in
    fonksiyonunu cagirir; bir parcada hata olsa bile digerleri donmeye devam eder
    (degerin yerine None gelir, Flutter null check yapar).
    """
    bundle = {
        "me": None,
        "state": None,
        "coaches": None,
        "daily_targets": None,
        "workout": None,
        "notifications": None,
        "water_today": None,
        "errors": {},  # debug icin: hangi parca neden bos kaldi
    }

    # me
    try:
        from app.api.client.me import client_me
        bundle["me"] = client_me(db=db, current_user=current_user)
    except Exception as e:
        bundle["errors"]["me"] = str(e)
        logger.warning(f"home-bundle me fetch failed: {e}")

    # state
    try:
        from app.api.client.state import get_client_state
        bundle["state"] = get_client_state(db=db, current_user=current_user)
    except Exception as e:
        bundle["errors"]["state"] = str(e)
        logger.warning(f"home-bundle state fetch failed: {e}")

    # coaches
    try:
        from app.api.client.coaches import get_coaches
        bundle["coaches"] = get_coaches(db=db, current_user=current_user)
    except Exception as e:
        bundle["errors"]["coaches"] = str(e)
        logger.warning(f"home-bundle coaches fetch failed: {e}")

    # daily_targets
    try:
        from app.api.client.daily_targets import get_daily_targets
        bundle["daily_targets"] = get_daily_targets(db=db, current_user=current_user)
    except Exception as e:
        bundle["errors"]["daily_targets"] = str(e)
        logger.warning(f"home-bundle daily_targets fetch failed: {e}")

    # workout (active program)
    try:
        from app.api.client.workouts import get_active_workout_for_client
        bundle["workout"] = get_active_workout_for_client(db=db, current_user=current_user)
    except HTTPException as e:
        # 404 normal — aktif program yok
        if e.status_code != 404:
            bundle["errors"]["workout"] = e.detail
            logger.warning(f"home-bundle workout fetch failed: {e.detail}")
    except Exception as e:
        bundle["errors"]["workout"] = str(e)
        logger.warning(f"home-bundle workout fetch failed: {e}")

    # notifications
    try:
        from app.api.client.notifications import get_client_notifications
        bundle["notifications"] = get_client_notifications(db=db, current_user=current_user)
    except Exception as e:
        bundle["errors"]["notifications"] = str(e)
        logger.warning(f"home-bundle notifications fetch failed: {e}")

    # water_today
    try:
        from app.api.client.water_intake import get_today_water
        bundle["water_today"] = get_today_water(db=db, current_user=current_user)
    except Exception as e:
        bundle["errors"]["water_today"] = str(e)
        logger.warning(f"home-bundle water_today fetch failed: {e}")

    # errors bos ise hic gondermeyelim (Flutter'i gereksiz yere uyandirmasin)
    if not bundle["errors"]:
        del bundle["errors"]

    return bundle
