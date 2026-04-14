"""Coach access to student body form photos + settings."""
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role

router = APIRouter()


def _verify_ownership(cur, student_user_id, current_user):
    # Superadmin bypasses ownership check
    if current_user.get("role") == "superadmin":
        return
    coach_id = current_user["id"]
    cur.execute(
        """SELECT 1 FROM clients WHERE user_id = %s AND assigned_coach_id = %s
           UNION
           SELECT 1 FROM subscriptions WHERE client_user_id = %s AND coach_user_id = %s AND status = 'active'""",
        (student_user_id, coach_id, student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Bu öğrenciye erişim yetkiniz yok.")


@router.get("/students/{student_user_id}/body-form-photos")
def get_student_body_form_photos(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach", "superadmin")),
):
    """Get a student's latest body form photos."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_ownership(cur, student_user_id, current_user)

    cur.execute("SELECT COALESCE(full_name, email) AS name FROM users WHERE id = %s", (student_user_id,))
    user_row = cur.fetchone()
    student_name = user_row["name"] if user_row else "Bilinmiyor"

    # Latest photos (one per angle)
    cur.execute(
        """SELECT DISTINCT ON (angle) id, angle, photo_url, created_at, batch_date
           FROM body_form_photos WHERE client_user_id = %s
           ORDER BY angle, created_at DESC""",
        (student_user_id,),
    )
    rows = cur.fetchall()
    last_updated = None
    for r in rows:
        if r.get("created_at"):
            ts = r["created_at"].isoformat()
            r["created_at"] = ts
            if last_updated is None or ts > last_updated:
                last_updated = ts
        if r.get("batch_date"):
            r["batch_date"] = r["batch_date"].isoformat()

    # Frequency setting
    cur.execute(
        "SELECT frequency_days FROM form_analysis_settings WHERE client_user_id = %s",
        (student_user_id,),
    )
    freq_row = cur.fetchone()
    frequency_days = freq_row["frequency_days"] if freq_row else 30

    return {
        "student_name": student_name,
        "photos": rows,
        "is_complete": len(rows) == 4,
        "last_updated": last_updated,
        "frequency_days": frequency_days,
    }


@router.get("/students/{student_user_id}/body-form-photos/history")
def get_student_body_form_history(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach", "superadmin")),
):
    """Get all form photo sets grouped by batch_date for timeline/comparison."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_ownership(cur, student_user_id, current_user)

    cur.execute(
        """SELECT id, angle, photo_url, created_at, batch_date
           FROM body_form_photos WHERE client_user_id = %s
           ORDER BY created_at DESC""",
        (student_user_id,),
    )
    all_photos = cur.fetchall()

    # Group by batch_date
    batches = {}
    for p in all_photos:
        bd = (p.get("batch_date") or p["created_at"][:10] if p.get("created_at") else "unknown")
        if hasattr(bd, 'isoformat'):
            bd = bd.isoformat()
        if bd not in batches:
            batches[bd] = {}
        angle = p["angle"]
        if angle not in batches[bd]:  # keep latest per angle per batch
            batches[bd][angle] = {
                "photo_url": p["photo_url"],
                "created_at": p["created_at"].isoformat() if hasattr(p.get("created_at"), 'isoformat') else p.get("created_at"),
            }

    # Convert to sorted list
    history = []
    for date_key in sorted(batches.keys(), reverse=True):
        history.append({
            "date": date_key,
            "photos": batches[date_key],
            "angle_count": len(batches[date_key]),
        })

    return {"history": history}


class FrequencyInput(BaseModel):
    frequency_days: int


@router.post("/students/{student_user_id}/body-form-settings")
def set_form_frequency(
    student_user_id: int,
    body: FrequencyInput,
    db=Depends(get_db),
    current_user=Depends(require_role("coach", "superadmin")),
):
    """Set how often the student should upload form photos."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_ownership(cur, student_user_id, current_user)

    freq = max(7, min(90, body.frequency_days))
    cur.execute(
        """INSERT INTO form_analysis_settings (client_user_id, coach_user_id, frequency_days)
           VALUES (%s, %s, %s)
           ON CONFLICT (client_user_id) DO UPDATE SET frequency_days = %s, updated_at = NOW()""",
        (student_user_id, current_user["id"], freq, freq),
    )
    db.commit()
    return {"ok": True, "frequency_days": freq}


@router.post("/students/{student_user_id}/body-form-request")
def request_form_photos(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach", "superadmin")),
):
    """Coach manually requests form photos from student — sends push notification."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_ownership(cur, student_user_id, current_user)

    # Get coach name
    cur.execute("SELECT full_name FROM users WHERE id = %s", (current_user["id"],))
    coach_row = cur.fetchone()
    coach_name = coach_row["full_name"] if coach_row else "Koçunuz"

    # Send push notification
    try:
        from app.services.push_notification import send_notification
        send_notification(
            student_user_id,
            "Form Fotoğrafı İstendi",
            f"{coach_name} güncel form fotoğraflarınızı bekliyor.",
            {"type": "form_request"},
        )
    except Exception:
        pass

    return {"ok": True, "message": "Bildirim gönderildi"}
