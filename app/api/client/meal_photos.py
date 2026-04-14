"""Meal photo tracking — stores photos separately from chat messages."""
from fastapi import Depends
from pydantic import BaseModel
from typing import Optional
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


class MealPhotoInput(BaseModel):
    meal_label: str
    photo_url: str
    is_retake: bool = False


@router.post("/meal-photos")
def save_meal_photo(
    body: MealPhotoInput,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Save meal photo record and notify coach."""
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

    return {"ok": True, "id": photo_id}


@router.get("/meal-photos/today")
def get_today_meal_photos(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Get client's meal photos uploaded today."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT id, meal_label, photo_url, is_retake, created_at
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
    """Get client's meal photos."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT id, meal_label, photo_url, is_retake, created_at
           FROM meal_photos WHERE client_user_id = %s
           ORDER BY created_at DESC LIMIT %s""",
        (current_user["id"], limit),
    )
    rows = cur.fetchall()
    for r in rows:
        r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else None
    return {"photos": rows}
