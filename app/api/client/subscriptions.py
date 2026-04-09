"""Client subscription management - cancel endpoint."""
from fastapi import Depends, HTTPException
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


@router.post("/subscriptions/cancel")
def cancel_subscription(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Cancel the client's active subscription.
    Sets status to 'canceled', keeps access until ends_at.
    """
    try:
        client_user_id = current_user["id"]
        cur = db.cursor()

        # Find active subscription
        cur.execute(
            """
            SELECT id, status, ends_at
            FROM subscriptions
            WHERE client_user_id = %s
              AND status IN ('active', 'pending')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (client_user_id,),
        )
        sub = cur.fetchone()

        if not sub:
            raise HTTPException(status_code=404, detail="Aktif abonelik bulunamadı")

        sub_id = sub["id"]

        # Cancel subscription
        cur.execute(
            "UPDATE subscriptions SET status = 'canceled', updated_at = NOW() WHERE id = %s",
            (sub_id,),
        )

        # Deactivate workout programs
        cur.execute(
            "UPDATE workout_programs SET is_active = FALSE, updated_at = NOW() WHERE client_user_id = %s AND is_active = TRUE",
            (client_user_id,),
        )

        # Deactivate nutrition programs
        cur.execute(
            "UPDATE nutrition_programs SET is_active = FALSE, updated_at = NOW() WHERE client_user_id = %s AND is_active = TRUE",
            (client_user_id,),
        )

        # Set assigned_coach_id to NULL so client becomes passive (NO_COACH)
        cur.execute(
            "UPDATE clients SET assigned_coach_id = NULL WHERE user_id = %s",
            (client_user_id,),
        )

        db.commit()
        return {"ok": True, "message": "Abonelik iptal edildi"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cancel error: {str(e)}")
