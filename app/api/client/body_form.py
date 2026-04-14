"""Body form analysis photos — 4 angle photos for coach review."""
from fastapi import Depends
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


class BodyFormPhotoInput(BaseModel):
    angle: str
    photo_url: str


VALID_ANGLES = ("front", "back", "left_side", "right_side")


@router.post("/body-form-photos")
def save_body_form_photo(
    body: BodyFormPhotoInput,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Save one angle photo. Retakes are new rows; latest is fetched via DISTINCT ON."""
    if body.angle not in VALID_ANGLES:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"Geçersiz açı: {body.angle}. Geçerli: {VALID_ANGLES}")

    cur = db.cursor(cursor_factory=RealDictCursor)

    # Get assigned coach (may be None)
    cur.execute("SELECT assigned_coach_id FROM clients WHERE user_id = %s", (current_user["id"],))
    client = cur.fetchone()
    coach_id = client["assigned_coach_id"] if client else None

    cur.execute(
        """INSERT INTO body_form_photos (client_user_id, coach_user_id, angle, photo_url)
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (current_user["id"], coach_id, body.angle, body.photo_url),
    )
    db.commit()
    return {"ok": True, "id": cur.fetchone()["id"]}


@router.get("/body-form-photos")
def get_body_form_photos(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Get latest form photos (one per angle, most recent)."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT DISTINCT ON (angle) id, angle, photo_url, created_at
           FROM body_form_photos
           WHERE client_user_id = %s
           ORDER BY angle, created_at DESC""",
        (current_user["id"],),
    )
    rows = cur.fetchall()
    last_updated = None
    for r in rows:
        if r.get("created_at"):
            ts = r["created_at"].isoformat()
            r["created_at"] = ts
            if last_updated is None or ts > last_updated:
                last_updated = ts

    return {
        "photos": rows,
        "is_complete": len(rows) == 4,
        "last_updated": last_updated,
    }


@router.get("/body-form-photos/status")
def get_body_form_status(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Status check: completion + frequency + whether new photos are due."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT COUNT(DISTINCT angle) AS cnt,
                  MAX(created_at) AS last_updated
           FROM body_form_photos
           WHERE client_user_id = %s""",
        (current_user["id"],),
    )
    row = cur.fetchone()
    cnt = row["cnt"] if row else 0
    last = row["last_updated"].isoformat() if row and row["last_updated"] else None

    # Check frequency setting — is a new form due?
    form_due = False
    frequency_days = 30
    cur.execute(
        "SELECT frequency_days FROM form_analysis_settings WHERE client_user_id = %s",
        (current_user["id"],),
    )
    freq_row = cur.fetchone()
    if freq_row:
        frequency_days = freq_row["frequency_days"]

    if last:
        from datetime import datetime, timedelta
        try:
            last_dt = datetime.fromisoformat(last)
            form_due = datetime.now(last_dt.tzinfo) - last_dt > timedelta(days=frequency_days)
        except Exception:
            form_due = True
    else:
        form_due = True  # Never uploaded

    return {
        "completed_angles": cnt,
        "is_complete": cnt == 4,
        "last_updated": last,
        "frequency_days": frequency_days,
        "form_due": form_due,
    }
