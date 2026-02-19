import logging
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import require_role
from .routes import router

logger = logging.getLogger(__name__)


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_photo_url: Optional[str] = None


@router.get("/me")
def client_me(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Get current client user profile.
    
    Critical: This endpoint is the single source of truth for onboarding_done status.
    The frontend uses this to decide whether to show onboarding flow or home.
    
    Behavior:
    - Always returns onboarding_done as a boolean (never None)
    - If clients row is missing, creates it with onboarding_done=false
    - Returns onboarding_done=true only if clients.onboarding_done is explicitly TRUE
    
    Test:
    - Call GET /client/me after login
    - Check response.client.onboarding_done is boolean (true/false, never null)
    - If onboarding_done=true, user should go to Home
    - If onboarding_done=false, user should go to Onboarding
    """
    user_id = current_user["id"]
    cur = db.cursor()
    
    # Ensure clients row exists (upsert if missing)
    # This handles edge cases where signup didn't create the row
    # Safety mechanism: if clients row is missing, create it with onboarding_done=false
    cur.execute(
        """
        INSERT INTO clients (user_id, onboarding_done)
        VALUES (%s, FALSE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )
    # Commit if we actually inserted (safety mechanism for edge cases)
    if cur.rowcount > 0:
        db.commit()
        logger.debug(f"[CLIENT_ME] Created missing clients row for user_id={user_id}")

    # Get user and client data
    cur.execute(
        """
        SELECT
            u.id as user_id,
            u.email,
            u.role,
            COALESCE(u.full_name, co.full_name) AS full_name,
            u.phone_number,
            u.profile_photo_url,
            c.onboarding_done,
            c.gender,
            c.goal_type,
            c.activity_level,
            c.assigned_coach_id
        FROM users u
        LEFT JOIN clients c ON c.user_id = u.id
        LEFT JOIN client_onboarding co ON co.user_id = u.id
        WHERE u.id = %s
        """,
        (user_id,),
    )

    row = cur.fetchone()

    if not row:
        logger.error(f"[CLIENT_ME] User not found for user_id={user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    # Extract onboarding_done - ensure it's always a boolean
    # NULL from LEFT JOIN means clients row doesn't exist -> False
    # Explicit FALSE -> False
    # Explicit TRUE -> True
    onboarding_done = bool(row["onboarding_done"]) if row["onboarding_done"] is not None else False
    
    logger.debug(f"[CLIENT_ME] user_id={user_id}, onboarding_done={onboarding_done} (raw={row['onboarding_done']})")

    # Client data
    client = {
        "onboarding_done": onboarding_done,  # Always boolean, never None
        "gender": row["gender"],
        "goal_type": row["goal_type"],
        "activity_level": row["activity_level"],
        "assigned_coach_id": row["assigned_coach_id"],
    }

    return {
        "user": {
            "id": row["user_id"],
            "email": row["email"],
            "role": row["role"],
            "full_name": row.get("full_name"),
            "phone_number": row.get("phone_number"),
            "profile_photo_url": row.get("profile_photo_url"),
        },
        "client": client,
    }


@router.put("/me")
def update_client_me(
    req: UpdateProfileRequest,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Update current client user profile.
    Only full_name and phone_number can be updated.
    """
    user_id = current_user["id"]
    cur = db.cursor()

    updates = []
    values = []

    if req.full_name is not None:
        updates.append("full_name = %s")
        values.append(req.full_name.strip() if req.full_name else None)

    if req.phone_number is not None:
        updates.append("phone_number = %s")
        values.append(req.phone_number.strip() if req.phone_number else None)

    if req.profile_photo_url is not None:
        updates.append("profile_photo_url = %s")
        values.append(req.profile_photo_url.strip() if req.profile_photo_url else None)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = NOW()")
    values.append(user_id)

    cur.execute(
        f"UPDATE users SET {', '.join(updates)} WHERE id = %s RETURNING id, email, full_name, phone_number, profile_photo_url",
        values,
    )
    row = cur.fetchone()
    db.commit()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"[CLIENT_ME] Profile updated for user_id={user_id}")

    return {
        "user": {
            "id": row["id"],
            "email": row["email"],
            "full_name": row.get("full_name"),
            "phone_number": row.get("phone_number"),
            "profile_photo_url": row.get("profile_photo_url"),
        },
    }
