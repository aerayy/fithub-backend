from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from app.core.database import get_db
from app.core.security import require_role

router = APIRouter()


@router.get("/me/profile")
def get_my_profile(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active
        FROM coaches
        WHERE user_id = %s
        """,
        (coach_id,),
    )
    row = cur.fetchone()

    if not row:
        cur.execute(
            """
            INSERT INTO coaches (user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active)
            VALUES (%s, '', NULL, NULL, 0, 0, ARRAY[]::text[], NULL, TRUE)
            RETURNING user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active
            """,
            (coach_id,),
        )
        row = cur.fetchone()
        db.commit()

    return {"profile": row}


@router.put("/me/profile")
def update_my_profile(
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    allowed_fields = {"bio", "photo_url", "price_per_month", "specialties", "instagram", "is_active"}
    updates = {k: payload.get(k) for k in payload.keys() if k in allowed_fields}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    set_parts = []
    values = []
    for k, v in updates.items():
        set_parts.append(f"{k}=%s")
        values.append(v)

    values.append(coach_id)

    cur.execute(
        f"""
        UPDATE coaches
        SET {", ".join(set_parts)}
        WHERE user_id = %s
        RETURNING user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active
        """,
        tuple(values),
    )

    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Coach profile not found")

    db.commit()
    return {"ok": True, "profile": row}
