"""Meal photo tracking — stores photos separately from chat messages.

AI analizi (BETA): GPT-4o-mini vision ile makro tahmini, save anında
background task olarak tetiklenir. Response bloklanmaz.
"""
import logging
from fastapi import BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional
from psycopg2.extras import RealDictCursor, Json
from app.core.database import get_db, _get_pool
from app.core.security import require_role
from app.services.badges import check_and_award
from app.services.meal_ai_analyzer import analyze_meal_photo
from .routes import router

logger = logging.getLogger(__name__)


def _run_ai_analysis(photo_id: int, photo_url: str, meal_label: str):
    """Background task — fotoğrafı analiz et, sonucu DB'ye yaz."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        cur = conn.cursor()
        # Status = processing
        cur.execute(
            "UPDATE meal_photos SET ai_analysis_status = 'processing' WHERE id = %s",
            (photo_id,),
        )
        conn.commit()

        result = analyze_meal_photo(photo_url, meal_label=meal_label)

        if result:
            cur.execute(
                """UPDATE meal_photos
                   SET ai_analysis = %s, ai_analysis_status = 'completed'
                   WHERE id = %s""",
                (Json(result), photo_id),
            )
            conn.commit()
            logger.info(f"[MEAL_AI] photo_id={photo_id} analizi tamamlandı")
        else:
            cur.execute(
                "UPDATE meal_photos SET ai_analysis_status = 'failed' WHERE id = %s",
                (photo_id,),
            )
            conn.commit()
            logger.warning(f"[MEAL_AI] photo_id={photo_id} analizi başarısız")
    except Exception as e:
        logger.error(f"[MEAL_AI] background task hatası: {e}", exc_info=True)
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE meal_photos SET ai_analysis_status = 'failed' WHERE id = %s",
                (photo_id,),
            )
            conn.commit()
        except Exception:
            pass
    finally:
        pool.putconn(conn)


class MealPhotoInput(BaseModel):
    meal_label: str
    photo_url: str
    is_retake: bool = False


@router.post("/meal-photos")
def save_meal_photo(
    body: MealPhotoInput,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Save meal photo record and notify coach. AI analizi background'da tetiklenir."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Get coach + client name for notification
    cur.execute(
        """SELECT c.assigned_coach_id, u.full_name
           FROM clients c JOIN users u ON u.id = c.user_id
           WHERE c.user_id = %s""",
        (current_user["id"],),
    )
    row = cur.fetchone()
    coach_id = row["assigned_coach_id"] if row else None
    client_name = row["full_name"] if row else "Öğrenci"

    cur.execute(
        """INSERT INTO meal_photos (client_user_id, coach_user_id, meal_label, photo_url, is_retake)
           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (current_user["id"], coach_id, body.meal_label, body.photo_url, body.is_retake),
    )
    db.commit()
    photo_id = cur.fetchone()["id"]

    # Notify coach via FCM push
    if coach_id:
        try:
            from app.services.push_notification import send_notification
            action = "güncelledi" if body.is_retake else "yükledi"
            send_notification(
                coach_id,
                "Öğün Fotoğrafı",
                f"{client_name} {body.meal_label} fotoğrafını {action}.",
                {"type": "meal_photo", "client_user_id": str(current_user["id"])},
            )
        except Exception:
            pass  # Push failure should not block the save

    # Activity log
    try:
        from app.services.activity_log import log_activity
        action = "güncelledi" if body.is_retake else "yükledi"
        log_activity(
            client_user_id=current_user["id"],
            coach_user_id=coach_id,
            action_type="meal_photo",
            title=f"{client_name} {body.meal_label} fotoğrafını {action}",
            photo_url=body.photo_url,
        )
    except Exception:
        pass

    # Award meal photo badge (fail-safe)
    newly_earned = []
    try:
        newly_earned = check_and_award(current_user["id"], 'meal_photo_sent', db)
    except Exception:
        pass

    # AI analizi — background task, response bloklanmaz (BETA özelliği)
    try:
        background_tasks.add_task(
            _run_ai_analysis,
            photo_id=photo_id,
            photo_url=body.photo_url,
            meal_label=body.meal_label,
        )
    except Exception:
        pass

    return {"ok": True, "id": photo_id, "newly_earned": newly_earned}


@router.get("/meal-photos/today")
def get_today_meal_photos(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Get client's meal photos uploaded today + AI analysis."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT id, meal_label, photo_url, is_retake, created_at,
                  ai_analysis, ai_analysis_status
           FROM meal_photos
           WHERE client_user_id = %s AND created_at::date = CURRENT_DATE
           ORDER BY created_at ASC""",
        (current_user["id"],),
    )
    rows = cur.fetchall()
    for r in rows:
        r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else None
    return {"photos": rows}


@router.get("/meal-photos")
def get_my_meal_photos(
    limit: int = 20,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Get client's meal photos + AI analysis."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT id, meal_label, photo_url, is_retake, created_at,
                  ai_analysis, ai_analysis_status
           FROM meal_photos WHERE client_user_id = %s
           ORDER BY created_at DESC LIMIT %s""",
        (current_user["id"], limit),
    )
    rows = cur.fetchall()
    for r in rows:
        r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else None
    return {"photos": rows}
