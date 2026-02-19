import logging
from fastapi import Depends, HTTPException
from app.core.database import get_db
from app.core.security import require_role
from .routes import router

logger = logging.getLogger(__name__)


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
        },
        "client": client,
    }
