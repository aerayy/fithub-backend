"""Coach activity feed — student action logs."""
from fastapi import APIRouter, Depends, Query
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role

router = APIRouter()


@router.get("/students/{student_user_id}/activity")
def get_student_activity(
    student_user_id: int,
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
    current_user=Depends(require_role("coach", "superadmin")),
):
    """Get activity log for a specific student."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """SELECT id, action_type, title, detail, photo_url, created_at
           FROM activity_log
           WHERE client_user_id = %s
           ORDER BY created_at DESC
           LIMIT %s""",
        (student_user_id, limit),
    )
    rows = cur.fetchall()
    for r in rows:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
    return {"activities": rows}
