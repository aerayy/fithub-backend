"""Coach view of student meal photos."""
from fastapi import Depends, Query
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


@router.get("/students/{student_user_id}/meal-photos")
def get_student_meal_photos(
    student_user_id: int,
    limit: int = Query(30, ge=1, le=200),
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Get meal photos for a specific student."""
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student belongs to this coach
    cur.execute(
        """SELECT 1 FROM clients WHERE user_id = %s AND assigned_coach_id = %s
           UNION
           SELECT 1 FROM subscriptions WHERE client_user_id = %s AND coach_user_id = %s LIMIT 1""",
        (student_user_id, coach_id, student_user_id, coach_id),
    )
    if not cur.fetchone():
        return {"photos": []}

    # Don't filter by coach_user_id in meal_photos — just by client
    cur.execute(
        """SELECT mp.id, mp.meal_label, mp.photo_url, mp.is_retake, mp.created_at,
                  mp.ai_analysis, mp.ai_analysis_status,
                  u.full_name as client_name
           FROM meal_photos mp
           JOIN users u ON u.id = mp.client_user_id
           WHERE mp.client_user_id = %s
           ORDER BY mp.created_at DESC LIMIT %s""",
        (student_user_id, limit),
    )
    rows = cur.fetchall()
    for r in rows:
        r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else None
    return {"photos": rows}


@router.get("/meal-photos/recent")
def get_recent_meal_photos(
    limit: int = Query(20, ge=1, le=50),
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Get most recent meal photos from all students of this coach."""
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """SELECT mp.id, mp.meal_label, mp.photo_url, mp.is_retake, mp.created_at,
                  mp.ai_analysis, mp.ai_analysis_status,
                  mp.client_user_id, u.full_name as client_name
           FROM meal_photos mp
           JOIN users u ON u.id = mp.client_user_id
           WHERE mp.coach_user_id = %s
           ORDER BY mp.created_at DESC LIMIT %s""",
        (coach_id, limit),
    )
    rows = cur.fetchall()
    for r in rows:
        r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else None
    return {"photos": rows}
