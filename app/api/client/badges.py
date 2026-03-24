"""Badge API endpoints for clients."""
from fastapi import Depends
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from app.services.badges import check_and_award
from .routes import router


@router.get("/badges")
def get_my_badges(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Get all badge definitions with user's earned status."""
    user_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Check membership badges on every load
    try:
        check_and_award(user_id, 'login', db)
    except Exception:
        pass

    cur.execute("""
        SELECT bd.id, bd.name_tr, bd.description_tr, bd.icon, bd.category, bd.sort_order,
               ub.earned_at
        FROM badge_definitions bd
        LEFT JOIN user_badges ub ON ub.badge_id = bd.id AND ub.user_id = %s
        ORDER BY bd.sort_order ASC
    """, (user_id,))

    rows = cur.fetchall()
    for r in rows:
        r["earned"] = r["earned_at"] is not None
        r["earned_at"] = r["earned_at"].isoformat() if r.get("earned_at") else None

    earned_count = sum(1 for r in rows if r["earned"])

    return {
        "badges": rows,
        "earned_count": earned_count,
        "total_count": len(rows),
    }


@router.get("/badges/new")
def check_new_badges(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Check for any newly earned badges (membership, etc.)."""
    newly = check_and_award(current_user["id"], 'login', db)
    return {"new_badges": newly}
