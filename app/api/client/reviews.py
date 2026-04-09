"""Coach review endpoints for clients."""
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


class ReviewInput(BaseModel):
    coach_user_id: int
    rating: int  # 1-5
    comment: Optional[str] = None


@router.post("/reviews")
def submit_review(
    body: ReviewInput,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Submit or update a coach review."""
    if body.rating < 1 or body.rating > 5:
        raise HTTPException(400, "Rating 1-5 arası olmalı")

    cur = db.cursor(cursor_factory=RealDictCursor)

    # Check if client has/had subscription with this coach
    cur.execute(
        "SELECT id FROM subscriptions WHERE client_user_id = %s AND coach_user_id = %s LIMIT 1",
        (current_user["id"], body.coach_user_id),
    )
    if not cur.fetchone():
        raise HTTPException(403, "Bu kocu degerlendirmek icin paket satin almis olmalisiniz")

    # Upsert review
    cur.execute(
        """INSERT INTO coach_reviews (client_user_id, coach_user_id, rating, comment)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (client_user_id, coach_user_id)
           DO UPDATE SET rating = EXCLUDED.rating, comment = EXCLUDED.comment, created_at = NOW()
           RETURNING id""",
        (current_user["id"], body.coach_user_id, body.rating, body.comment),
    )
    review_id = cur.fetchone()["id"]

    # Update coach's aggregate rating
    cur.execute(
        """UPDATE coaches SET
           rating = (SELECT COALESCE(AVG(rating), 0) FROM coach_reviews WHERE coach_user_id = %s),
           rating_count = (SELECT COUNT(*) FROM coach_reviews WHERE coach_user_id = %s)
           WHERE user_id = %s""",
        (body.coach_user_id, body.coach_user_id, body.coach_user_id),
    )

    db.commit()
    return {"ok": True, "id": review_id}


@router.get("/reviews/{coach_user_id}")
def get_coach_reviews(
    coach_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("client", "coach")),
):
    """Get all reviews for a coach."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT cr.id, cr.rating, cr.comment, cr.created_at, u.full_name as client_name
           FROM coach_reviews cr
           JOIN users u ON u.id = cr.client_user_id
           WHERE cr.coach_user_id = %s
           ORDER BY cr.created_at DESC""",
        (coach_user_id,),
    )
    rows = cur.fetchall()
    for r in rows:
        r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else None
    return {"reviews": rows}
