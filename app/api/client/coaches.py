import traceback
from fastapi import Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from psycopg2.extras import RealDictCursor

from app.core.database import get_db
from app.core.security import require_role
from .routes import router


@router.get("/coaches")
def get_coaches(
    q: str = Query(None, description="Search query (searches in full_name, bio, specialties)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Get list of active coaches with optional search and pagination.
    
    Returns coaches where is_active = true, ordered by rating DESC, rating_count DESC, user_id ASC.
    
    Query params:
    - q: Optional search query (searches in full_name, bio, specialties)
    - limit: Maximum number of results (default: 20, max: 100)
    - offset: Number of results to skip (default: 0)
    
    Example curl test:
    curl -X GET "http://localhost:8000/client/coaches?q=fitness&limit=5&offset=0" \
      -H "Authorization: Bearer YOUR_TOKEN"
    """
    cur = db.cursor(cursor_factory=RealDictCursor)
    
    # Build WHERE clause with search
    where_clauses = ["c.is_active = TRUE"]
    params = []
    
    if q:
        search_term = f"%{q.lower()}%"
        where_clauses.append(
            """(
                LOWER(u.full_name) LIKE %s OR
                LOWER(c.bio) LIKE %s OR
                EXISTS (
                    SELECT 1 FROM unnest(c.specialties) AS specialty
                    WHERE LOWER(specialty) LIKE %s
                )
            )"""
        )
        params.extend([search_term, search_term, search_term])
    
    where_sql = " AND ".join(where_clauses)
    
    # Get total count for pagination
    cur.execute(
        f"""
        SELECT COUNT(*) as total
        FROM coaches c
        JOIN users u ON u.id = c.user_id
        WHERE {where_sql}
        """,
        tuple(params)
    )
    total = cur.fetchone()["total"]
    
    # Get paginated results
    cur.execute(
        f"""
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
        WHERE {where_sql}
        ORDER BY c.rating DESC NULLS LAST,
                 c.rating_count DESC NULLS LAST,
                 c.user_id ASC
        LIMIT %s OFFSET %s
        """,
        tuple(params) + (limit, offset)
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
            "price_per_month": float(row["price_per_month"]) if row.get("price_per_month") is not None else None,
            "rating": float(row["rating"]) if row.get("rating") is not None else None,
            "rating_count": row.get("rating_count") or 0,  # Default to 0 if NULL
            "specialties": row.get("specialties") or [],  # Default to empty array if NULL
            "instagram": row.get("instagram"),
            "is_active": row.get("is_active", True),  # Default to True if NULL
        })
    
    return {
        "coaches": coaches,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/coaches/{coach_user_id}")
def get_coach_detail(
    coach_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Get detailed coach profile including active packages.

    Example curl test:
    curl -X GET "http://localhost:8000/client/coaches/123" \
      -H "Authorization: Bearer YOUR_TOKEN"
    """
    try:
        cur = db.cursor(cursor_factory=RealDictCursor)

        # Get coach profile
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
                c.is_active,
                c.title,
                c.photos,
                c.certificates,
                c.twitter,
                c.linkedin,
                c.website
            FROM coaches c
            JOIN users u ON u.id = c.user_id
            WHERE c.user_id = %s AND c.is_active = TRUE
            """,
            (coach_user_id,)
        )

        coach_row = cur.fetchone()
        if not coach_row:
            raise HTTPException(status_code=404, detail="Coach not found or inactive")

        # Get active packages
        cur.execute(
            """
            SELECT
                id,
                coach_user_id,
                name,
                description,
                duration_days,
                price,
                discount_percentage,
                is_active,
                services,
                image_url,
                created_at,
                updated_at
            FROM coach_packages
            WHERE coach_user_id = %s AND is_active = TRUE
            ORDER BY price ASC, created_at DESC
            """,
            (coach_user_id,)
        )

        package_rows = cur.fetchall() or []
        packages = []
        for p in package_rows:
            packages.append({
                "id": p["id"],
                "coach_user_id": p["coach_user_id"],
                "name": p.get("name"),
                "description": p.get("description"),
                "duration_days": p.get("duration_days"),
                "price": float(p["price"]) if p.get("price") is not None else None,
                "discount_percentage": float(p["discount_percentage"]) if p.get("discount_percentage") is not None else 0,
                "is_active": p.get("is_active", True),
                "services": p.get("services") or [],
                "created_at": p["created_at"].isoformat() if p.get("created_at") else None,
                "updated_at": p["updated_at"].isoformat() if p.get("updated_at") else None,
            })

        coach = {
            "user_id": coach_row["user_id"],
            "full_name": coach_row.get("full_name"),
            "bio": coach_row.get("bio"),
            "photo_url": coach_row.get("photo_url"),
            "price_per_month": float(coach_row["price_per_month"]) if coach_row.get("price_per_month") is not None else None,
            "rating": float(coach_row["rating"]) if coach_row.get("rating") is not None else None,
            "rating_count": coach_row.get("rating_count") or 0,
            "specialties": coach_row.get("specialties") or [],
            "instagram": coach_row.get("instagram"),
            "is_active": coach_row.get("is_active", True),
            "title": coach_row.get("title"),
            "photos": coach_row.get("photos") or [],
            "certificates": coach_row.get("certificates") or [],
            "twitter": coach_row.get("twitter"),
            "linkedin": coach_row.get("linkedin"),
            "website": coach_row.get("website"),
        }

        return {
            "coach": coach,
            "packages": packages
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[coaches] get_coach_detail ERROR: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal error: {str(e)}"}
        )
