from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError
from datetime import datetime
from app.core.security import require_role
from app.core.database import get_db
from app.schemas.subscriptions import SubscriptionConfirmRequest, SubscriptionConfirmResponse

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/ping")
def subscriptions_ping():
    """Health check endpoint for subscriptions router"""
    return {"ok": True, "message": "subscriptions router works"}


@router.post("/confirm", response_model=SubscriptionConfirmResponse)
def confirm_subscription(
    request: SubscriptionConfirmRequest,
    current_user=Depends(require_role("client")),
    db=Depends(get_db)
):
    """
    Confirm and persist subscription in database.
    Idempotent: if subscription already exists for this client_user_id and subscription_ref,
    returns existing record instead of creating duplicate.
    """
    print("subscription_confirm hit")  # Log at start
    client_user_id = current_user["id"]
    coach_id = request.coach_id
    plan_id = request.plan_id
    subscription_ref = request.subscription_ref
    
    # Log the attempt
    print(f"subscription_confirm: user={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref}")
    
    cur = db.cursor(cursor_factory=RealDictCursor)
    
    # Check if subscription already exists (idempotency)
    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, plan_name, subscription_ref, status, started_at
        FROM subscriptions
        WHERE client_user_id = %s AND subscription_ref = %s
        """,
        (client_user_id, subscription_ref)
    )
    existing_subscription = cur.fetchone()
    
    if existing_subscription:
        # Return existing subscription
        print(f"subscription_confirm: user={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref} created=False (existing)")
        return SubscriptionConfirmResponse(
            ok=True,
            subscription={
                "id": existing_subscription["id"],
                "client_user_id": existing_subscription["client_user_id"],
                "coach_id": str(existing_subscription["coach_user_id"]),
                "plan_id": existing_subscription.get("plan_name") or plan_id,
                "subscription_ref": existing_subscription["subscription_ref"],
                "status": existing_subscription["status"],
                "started_at": existing_subscription["started_at"].isoformat() if existing_subscription["started_at"] else None,
            },
            created=False
        )
    
    # Create new subscription
    try:
        # coach_id string olarak geliyor, integer'a çevir
        try:
            coach_user_id = int(coach_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid coach_id: {coach_id}"
            )
        
        cur.execute(
            """
            INSERT INTO subscriptions (
                client_user_id,
                coach_user_id,
                plan_name,
                subscription_ref,
                status,
                started_at,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING id, client_user_id, coach_user_id, plan_name, subscription_ref, status, started_at
            """,
            (
                client_user_id,
                coach_user_id,
                plan_id,
                subscription_ref,
                "active",
                datetime.utcnow()
            )
        )
        
        new_subscription = cur.fetchone()
        db.commit()  # Explicit commit after insert
        
        print(f"subscription_confirm: user={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref} created=True")
        
        return SubscriptionConfirmResponse(
            ok=True,
            subscription={
                "id": new_subscription["id"],
                "client_user_id": new_subscription["client_user_id"],
                "coach_id": str(new_subscription["coach_user_id"]),
                "plan_id": new_subscription.get("plan_name") or plan_id,
                "subscription_ref": new_subscription["subscription_ref"],
                "status": new_subscription["status"],
                "started_at": new_subscription["started_at"].isoformat() if new_subscription["started_at"] else None,
            },
            created=True
        )
        
    except IntegrityError as e:
        db.rollback()
        # Handle unique constraint violation (race condition)
        cur.execute(
            """
            SELECT id, client_user_id, coach_user_id, plan_name, subscription_ref, status, started_at
            FROM subscriptions
            WHERE client_user_id = %s AND subscription_ref = %s
            """,
            (client_user_id, subscription_ref)
        )
        existing_subscription = cur.fetchone()
        
        if existing_subscription:
            print(f"subscription_confirm: user={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref} created=False (race condition)")
            return SubscriptionConfirmResponse(
                ok=True,
                subscription={
                    "id": existing_subscription["id"],
                    "client_user_id": existing_subscription["client_user_id"],
                    "coach_id": str(existing_subscription["coach_user_id"]),
                    "plan_id": existing_subscription.get("plan_name") or plan_id,
                    "subscription_ref": existing_subscription["subscription_ref"],
                    "status": existing_subscription["status"],
                    "started_at": existing_subscription["started_at"].isoformat() if existing_subscription["started_at"] else None,
                },
                created=False
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create subscription: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        print(f"subscription_confirm: ERROR user={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref} error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
