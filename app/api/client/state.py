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
    Get the current state of the client based on their latest subscription.
    
    Returns:
    - NO_COACH: No subscription or subscription is canceled/rejected
    - EXPIRED: Subscription has expired
    - PURCHASED_WAITING: Subscription is pending/active but program not assigned yet
    - PROGRAM_ASSIGNED: Subscription is pending/active and program is assigned
    - UNKNOWN: Unexpected state
    """
    client_user_id = current_user["id"]
    cur = db.cursor()
    
    try:
        # Get latest subscription for this client
        cur.execute(
            """
            SELECT 
                id, 
                status, 
                purchased_at, 
                started_at, 
                ends_at, 
                program_assigned_at, 
                coach_user_id, 
                package_id
            FROM subscriptions
            WHERE client_user_id = %s
            ORDER BY purchased_at DESC
            LIMIT 1
            """,
            (client_user_id,),
        )
        
        subscription_row = cur.fetchone()
        
        # Determine state
        if subscription_row is None:
            state = "NO_COACH"
            subscription = None
        else:
            status = subscription_row["status"]
            
            # Convert subscription row to dict
            subscription = dict(subscription_row)
            
            # Convert datetime fields to ISO format if they exist
            for field in ["purchased_at", "started_at", "ends_at", "program_assigned_at"]:
                if subscription.get(field) is not None and isinstance(subscription[field], datetime):
                    subscription[field] = subscription[field].isoformat()
            
            # State mapping logic (in order of priority)
            if status in ("canceled", "rejected"):
                state = "NO_COACH"
            elif status == "expired":
                state = "EXPIRED"
            elif subscription_row["ends_at"] is not None:
                # Check if ends_at is in the past
                ends_at = subscription_row["ends_at"]
                # Make timezone-aware if naive
                if ends_at.tzinfo is None:
                    ends_at = ends_at.replace(tzinfo=timezone.utc)
                if ends_at < datetime.now(timezone.utc):
                    state = "EXPIRED"
                elif status in ("pending", "active"):
                    # Check program_assigned_at
                    if subscription_row["program_assigned_at"] is None:
                        state = "PURCHASED_WAITING"
                    else:
                        state = "PROGRAM_ASSIGNED"
                else:
                    state = "UNKNOWN"
            elif status in ("pending", "active"):
                # status is pending/active and ends_at is NULL or not expired
                if subscription_row["program_assigned_at"] is None:
                    state = "PURCHASED_WAITING"
                else:
                    state = "PROGRAM_ASSIGNED"
            else:
                state = "UNKNOWN"
        
        return {
            "state": state,
            "subscription": subscription
        }
        
    except Exception as e:
        logger.error(f"Error getting client state for user_id={client_user_id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get client state: {str(e)}"
        )
