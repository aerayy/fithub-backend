from fastapi import Depends
from psycopg2.extras import RealDictCursor

from app.core.database import get_db
from app.core.security import require_role
from .routes import router


@router.get("/coaches")
def get_coaches(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Get list of active coaches.
    
    Returns coaches where is_active = true, ordered by rating DESC, rating_count DESC, user_id ASC.
    
    Example curl test:
    curl -X GET "http://localhost:8000/client/coaches" \
      -H "Authorization: Bearer YOUR_TOKEN"
    """
    cur = db.cursor(cursor_factory=RealDictCursor)
    
    cur.execute(
        """
        SELECT
            c.user_id,
            u.full_name,
            c.bio,
            c.photo_url,
            c.price_per_month,
            c.rating,
            c.rating_count,
            c.specialties,
            c.instagram,
            c.is_active
        FROM coaches c
        JOIN users u ON u.id = c.user_id
        WHERE c.is_active = TRUE
        ORDER BY c.rating DESC NULLS LAST,
                 c.rating_count DESC NULLS LAST,
                 c.user_id ASC
        """
    )
    
    rows = cur.fetchall() or []
    
    # RealDictCursor already returns dicts, just handle NULL values safely
    coaches = []
    for row in rows:
        coaches.append({
            "user_id": row["user_id"],
            "full_name": row.get("full_name"),  # Handle NULL safely
            "bio": row.get("bio"),
            "photo_url": row.get("photo_url"),
            "price_per_month": row.get("price_per_month"),  # Already numeric or None
            "rating": row.get("rating"),  # Already numeric or None
            "rating_count": row.get("rating_count") or 0,  # Default to 0 if NULL
            "specialties": row.get("specialties") or [],  # Default to empty array if NULL
            "instagram": row.get("instagram"),
            "is_active": row.get("is_active", True),  # Default to True if NULL
        })
    
    return {"coaches": coaches}
