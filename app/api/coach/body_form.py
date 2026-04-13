"""Coach access to student body form photos."""
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role

router = APIRouter()


@router.get("/students/{student_user_id}/body-form-photos")
def get_student_body_form_photos(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Get a student's latest body form photos (coach must own the student)."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify ownership: student is assigned to this coach OR has an active subscription
    cur.execute(
        """SELECT 1 FROM clients WHERE user_id = %s AND assigned_coach_id = %s
           UNION
           SELECT 1 FROM subscriptions WHERE student_user_id = %s AND coach_user_id = %s AND status = 'active'""",
        (student_user_id, current_user["id"], student_user_id, current_user["id"]),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Bu öğrenciye erişim yetkiniz yok.")

    # Get student name
    cur.execute(
        "SELECT COALESCE(full_name, email) AS name FROM users WHERE id = %s",
        (student_user_id,),
    )
    user_row = cur.fetchone()
    student_name = user_row["name"] if user_row else "Bilinmiyor"

    # Get latest photos
    cur.execute(
        """SELECT DISTINCT ON (angle) id, angle, photo_url, created_at
           FROM body_form_photos
           WHERE client_user_id = %s
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

    return {
        "student_name": student_name,
        "photos": rows,
        "is_complete": len(rows) == 4,
        "last_updated": last_updated,
    }
