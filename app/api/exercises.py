from fastapi import APIRouter, Depends, Query
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/search")
def search_exercises(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    db=Depends(get_db),
    current_user=Depends(require_role("coach", "client", "superadmin")),
):
    """
    Admin panel / AI / koç için:
    /exercises/search?q=push&limit=20
    """
    cur = db.cursor(cursor_factory=RealDictCursor)
    like = f"%{q}%"

    cur.execute(
        """
        SELECT
            id,
            external_id,
            canonical_name AS name,
            level,
            equipment,
            category,
            primary_muscles,
            secondary_muscles,
            gif_url
        FROM exercise_library
        WHERE
            canonical_name ILIKE %s
            OR external_id ILIKE %s
            OR (aliases IS NOT NULL AND EXISTS (
                SELECT 1
                FROM unnest(aliases) a
                WHERE a ILIKE %s
            ))
        ORDER BY
            CASE WHEN canonical_name ILIKE %s THEN 0
                 WHEN canonical_name ILIKE %s THEN 1
                 ELSE 2 END,
            canonical_name ASC
        LIMIT %s
        """,
        (like, like, like, q, f"{q}%", limit),
    )

    rows = cur.fetchall() or []
    return {"exercises": rows, "count": len(rows)}


@router.get("/detail")
def get_exercise_detail(
    name: str = Query("", min_length=0),
    id: int = Query(None),
    db=Depends(get_db),
    current_user=Depends(require_role("coach", "client", "superadmin")),
):
    """
    Get full exercise details by ID or name.
    /exercises/detail?id=303
    /exercises/detail?name=Bench Press
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    _FIELDS = """id, external_id, canonical_name, level, equipment, category,
                 primary_muscles, secondary_muscles, instructions,
                 instructions_tr, tips, image_urls, gif_url"""

    row = None

    # 1. Direct ID lookup (fastest, most accurate)
    if id is not None:
        cur.execute(f"SELECT {_FIELDS} FROM exercise_library WHERE id = %s", (id,))
        row = cur.fetchone()

    # 2. Exact name match
    if not row and name:
        cur.execute(f"SELECT {_FIELDS} FROM exercise_library WHERE canonical_name ILIKE %s LIMIT 1", (name,))
        row = cur.fetchone()

    # 3. Fuzzy name match
    if not row and name:
        cur.execute(
            f"""SELECT {_FIELDS} FROM exercise_library
            WHERE canonical_name ILIKE %s
               OR (aliases IS NOT NULL AND EXISTS (
                   SELECT 1 FROM unnest(aliases) a WHERE a ILIKE %s))
            ORDER BY
                CASE WHEN canonical_name ILIKE %s THEN 0
                     WHEN canonical_name ILIKE %s THEN 1
                     ELSE 2 END,
                length(canonical_name) ASC
            LIMIT 1""",
            (f"%{name}%", f"%{name}%", name, f"{name}%"),
        )
        row = cur.fetchone()

    if not row:
        return {"found": False, "exercise": None}

    return {
        "found": True,
        "exercise": row,
    }
