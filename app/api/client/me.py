from fastapi import Depends
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


@router.get("/me")
def client_me(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    cur = db.cursor()

    # clients tablosu yoksa bile user döndürerek patlamasın diye LEFT JOIN
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

    # row dict gibi dönüyor (RealDictCursor ise)
    return {
        "user": {
            "id": row["user_id"],
            "email": row["email"],
            "role": row["role"],
        },
        "client": {
            "onboarding_done": row.get("onboarding_done", False),
            "gender": row.get("gender"),
            "goal_type": row.get("goal_type"),
            "activity_level": row.get("activity_level"),
            "assigned_coach_id": row.get("assigned_coach_id"),
        },
    }
