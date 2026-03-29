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
    """Save meal photo record."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Get coach
    cur.execute("SELECT assigned_coach_id FROM clients WHERE user_id = %s", (current_user["id"],))
    client = cur.fetchone()
    coach_id = client["assigned_coach_id"] if client else None

    cur.execute(
        """INSERT INTO meal_photos (client_user_id, coach_user_id, meal_label, photo_url, is_retake)
           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (current_user["id"], coach_id, body.meal_label, body.photo_url, body.is_retake),
    )
    db.commit()
    return {"ok": True, "id": cur.fetchone()["id"]}


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
