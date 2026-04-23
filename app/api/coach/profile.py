import secrets
import string
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from app.core.database import get_db
from app.core.security import require_role


def _generate_referral_code(cur, full_name: str) -> str:
    """Generate a unique referral code from coach name + random digits."""
    # Take first part of name, uppercase, max 6 chars
    base = ''.join(c for c in (full_name or 'COACH').split()[0].upper() if c.isalpha())[:6]
    for _ in range(20):  # max 20 attempts
        suffix = ''.join(secrets.choice(string.digits) for _ in range(2))
        code = f"{base}{suffix}"
        cur.execute("SELECT 1 FROM coaches WHERE referral_code = %s", (code,))
        if not cur.fetchone():
            return code
    # Fallback: fully random
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

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
        SELECT c.user_id, c.bio, c.photo_url, c.price_per_month, c.rating, c.rating_count,
               c.specialties, c.instagram, c.is_active, c.referral_code,
               c.title, c.twitter, c.linkedin, c.website, c.photos, c.certificates,
               u.full_name, u.email
        FROM coaches c
        JOIN users u ON u.id = c.user_id
        WHERE c.user_id = %s
        """,
        (coach_id,),
    )
    row = cur.fetchone()

    if not row:
        # Get name for referral code generation
        cur.execute("SELECT full_name FROM users WHERE id = %s", (coach_id,))
        user = cur.fetchone()
        code = _generate_referral_code(cur, user["full_name"] if user else "COACH")
        cur.execute(
            """
            INSERT INTO coaches (user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active, referral_code)
            VALUES (%s, '', NULL, NULL, 0, 0, ARRAY[]::text[], NULL, TRUE, %s)
            RETURNING user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active, referral_code
            """,
            (coach_id, code),
        )
        row = cur.fetchone()
        db.commit()
    elif not row.get("referral_code"):
        # Auto-generate referral code for existing coach without one
        code = _generate_referral_code(cur, row.get("full_name", "COACH"))
        cur.execute("UPDATE coaches SET referral_code = %s WHERE user_id = %s", (code, coach_id))
        db.commit()
        row = dict(row)
        row["referral_code"] = code

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
