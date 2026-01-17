# app/api/client/state.py
import logging
from datetime import datetime, timezone

from fastapi import Depends, HTTPException

from app.core.database import get_db
from app.core.security import require_role
from .routes import router

logger = logging.getLogger(__name__)


@router.get("/state")
def get_client_state(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Client Home state (single source of truth):
    - NO_COACH: clients.assigned_coach_id is NULL  (coach yok)
    - EXPIRED: coach var ama aktif subscription yok ve son subscription expired / ends_at geçmiş
    - PURCHASED_WAITING: aktif subscription var ama program_assigned_at NULL ve program_state != 'assigned'
    - PROGRAM_ASSIGNED: aktif subscription var ve (program_state='assigned' veya program_assigned_at dolu)
    """
    client_user_id = current_user["id"]
    cur = db.cursor()

    try:
        # 1) Client'ın assigned_coach_id'sini al
        cur.execute(
            """
            SELECT assigned_coach_id
            FROM clients
            WHERE user_id = %s
            """,
            (client_user_id,),
        )
        client_row = cur.fetchone()
        assigned_coach_id = client_row["assigned_coach_id"] if client_row else None

        # Coach yoksa direkt NO_COACH
        if assigned_coach_id is None:
            return {"state": "NO_COACH", "subscription": None}

        # 2) Önce aktif subscription'ı bul (tek kaynak)
        cur.execute(
            """
            SELECT
                id,
                status,
                purchased_at,
                started_at,
                ends_at,
                program_assigned_at,
                program_state,
                coach_user_id,
                package_id
            FROM subscriptions
            WHERE client_user_id = %s
              AND coach_user_id = %s
              AND status = 'active'
              AND (ends_at IS NULL OR ends_at > NOW())
            ORDER BY purchased_at DESC NULLS LAST, id DESC
            LIMIT 1
            """,
            (client_user_id, assigned_coach_id),
        )
        subscription_row = cur.fetchone()

        # 3) Aktif subscription yoksa: expired mı değil mi anlamak için son kaydı çek
        if subscription_row is None:
            cur.execute(
                """
                SELECT
                    id,
                    status,
                    purchased_at,
                    started_at,
                    ends_at,
                    program_assigned_at,
                    program_state,
                    coach_user_id,
                    package_id
                FROM subscriptions
                WHERE client_user_id = %s
                  AND coach_user_id = %s
                ORDER BY purchased_at DESC NULLS LAST, id DESC
                LIMIT 1
                """,
                (client_user_id, assigned_coach_id),
            )
            last_row = cur.fetchone()

            if last_row is None:
                return {"state": "NO_COACH", "subscription": None}

            ends_at = last_row["ends_at"]
            is_expired = (last_row["status"] == "expired")

            if ends_at is not None:
                # Make timezone-aware if naive
                if ends_at.tzinfo is None:
                    ends_at = ends_at.replace(tzinfo=timezone.utc)
                if ends_at < datetime.now(timezone.utc):
                    is_expired = True

            subscription = dict(last_row)
            for field in ["purchased_at", "started_at", "ends_at", "program_assigned_at"]:
                if subscription.get(field) is not None and isinstance(subscription[field], datetime):
                    subscription[field] = subscription[field].isoformat()

            return {"state": "EXPIRED" if is_expired else "NO_COACH", "subscription": subscription}

        # 4) Burada subscription_row kesin: status=active ve ends_at geçmemiş
        subscription = dict(subscription_row)
        for field in ["purchased_at", "started_at", "ends_at", "program_assigned_at"]:
            if subscription.get(field) is not None and isinstance(subscription[field], datetime):
                subscription[field] = subscription[field].isoformat()

        program_state = subscription_row.get("program_state")
        if program_state == "assigned" or subscription_row["program_assigned_at"] is not None:
            state = "PROGRAM_ASSIGNED"
        else:
            state = "PURCHASED_WAITING"

        return {"state": state, "subscription": subscription}

    except Exception as e:
        logger.error(
            f"Error getting client state for user_id={client_user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get client state: {str(e)}")
