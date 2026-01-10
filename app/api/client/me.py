from fastapi import Depends, HTTPException
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


@router.get("/me")
def client_me(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    cur = db.cursor()

    cur.execute(
        """
        SELECT
            u.id as user_id,
            u.email,
            u.role,
            c.onboarding_done,
            c.gender,
            c.goal_type,
            c.activity_level,
            c.assigned_coach_id
        FROM users u
        LEFT JOIN clients c ON c.user_id = u.id
        WHERE u.id = %s
        """,
        (current_user["id"],),
    )

    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    # Client data - defaults to False/null if clients row doesn't exist (shouldn't happen with new signups)
    client = {
        "onboarding_done": row["onboarding_done"] if row["onboarding_done"] is not None else False,
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
        },
        "client": client,
    }
