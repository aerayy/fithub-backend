from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError
from datetime import datetime, timedelta
from typing import Optional
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
    coachId: Optional[str] = Query(None, alias="coachId", description="Coach ID from query param"),
    planId: Optional[str] = Query(None, alias="planId", description="Plan/Package ID from query param"),
    subscriptionId: Optional[str] = Query(None, alias="subscriptionId", description="Subscription ID from payment provider"),
    request: Optional[SubscriptionConfirmRequest] = Body(None, description="Request body (alternative to query params)"),
    current_user=Depends(require_role("client")),
    db=Depends(get_db)
):
    """
    Confirm and persist subscription in database after checkout success.
    Supports both query params (coachId, planId, subscriptionId) and request body.
    Idempotent: if subscription already exists for this client_user_id and subscription_ref,
    returns existing record instead of creating duplicate.
    """
    print("subscription_confirm hit")  # Log at start
    
    # Extract parameters from query params or request body
    if coachId and planId and subscriptionId:
        # Query params (Flutter web checkout success)
        coach_id = coachId
        plan_id = planId
        subscription_ref = subscriptionId
    elif request:
        # Request body (backward compatible)
        coach_id = request.coach_id
        plan_id = request.plan_id
        subscription_ref = request.subscription_ref
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either query params (coachId, planId, subscriptionId) or request body must be provided"
        )
    
    client_user_id = current_user["id"]
    
    # Log the attempt
    print(f"subscription_confirm: user={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref}")
    
    cur = db.cursor(cursor_factory=RealDictCursor)
    
    # Check if subscription already exists (idempotency)
    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, package_id, plan_name, subscription_ref, status, started_at, ends_at
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
                "package_id": existing_subscription.get("package_id"),
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
        
        # plan_id string olarak geliyor, package_id'ye çevir (eğer integer ise direkt kullan)
        package_id = None
        plan_name = plan_id  # Default: plan_id string'i plan_name olarak kullan
        duration_days = None
        ends_at = None
        
        try:
            # Try to parse planId as integer (it might be package_id)
            package_id_int = int(plan_id)
            
            # Check if package exists and get details
            cur.execute(
                """
                SELECT id, name, duration_days, coach_user_id
                FROM coach_packages
                WHERE id = %s
                """,
                (package_id_int,)
            )
            package_info = cur.fetchone()
            
            if package_info:
                # Verify package belongs to the coach
                if package_info["coach_user_id"] != coach_user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Package {package_id_int} does not belong to coach {coach_user_id}"
                    )
                package_id = package_id_int
                plan_name = package_info["name"]  # Use package name as plan_name
                duration_days = package_info.get("duration_days")
                
                # Calculate ends_at if duration_days exists
                if duration_days:
                    started_at = datetime.utcnow()
                    ends_at = started_at + timedelta(days=duration_days)
        except ValueError:
            # plan_id is not an integer, use it as plan_name string
            pass
        
        # Get current timestamp
        now = datetime.utcnow()
        started_at = now
        
        # Insert subscription
        cur.execute(
            """
            INSERT INTO subscriptions (
                client_user_id,
                coach_user_id,
                package_id,
                plan_name,
                subscription_ref,
                status,
                purchased_at,
                started_at,
                ends_at,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, client_user_id, coach_user_id, package_id, plan_name, subscription_ref, status, started_at, ends_at, purchased_at
            """,
            (
                client_user_id,
                coach_user_id,
                package_id,
                plan_name,
                subscription_ref,
                "active",  # Checkout success means subscription is active
                now,  # purchased_at
                started_at,
                ends_at,
                now,  # created_at
                now   # updated_at
            )
        )
        
        new_subscription = cur.fetchone()
        db.commit()  # Explicit commit after insert
        
        print(f"subscription_confirm: user={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref} created=True id={new_subscription['id']}")
        
        return SubscriptionConfirmResponse(
            ok=True,
            subscription={
                "id": new_subscription["id"],
                "client_user_id": new_subscription["client_user_id"],
                "coach_id": str(new_subscription["coach_user_id"]),
                "package_id": new_subscription.get("package_id"),
                "plan_id": new_subscription.get("plan_name") or plan_id,
                "subscription_ref": new_subscription["subscription_ref"],
                "status": new_subscription["status"],
                "started_at": new_subscription["started_at"].isoformat() if new_subscription["started_at"] else None,
                "ends_at": new_subscription["ends_at"].isoformat() if new_subscription["ends_at"] else None,
                "purchased_at": new_subscription["purchased_at"].isoformat() if new_subscription["purchased_at"] else None,
            },
            created=True
        )
        
    except IntegrityError as e:
        db.rollback()
        # Handle unique constraint violation (race condition)
        cur.execute(
            """
            SELECT id, client_user_id, coach_user_id, package_id, plan_name, subscription_ref, status, started_at, ends_at
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
                    "package_id": existing_subscription.get("package_id"),
                    "plan_id": existing_subscription.get("plan_name") or plan_id,
                    "subscription_ref": existing_subscription["subscription_ref"],
                    "status": existing_subscription["status"],
                    "started_at": existing_subscription["started_at"].isoformat() if existing_subscription["started_at"] else None,
                },
                created=False
            )
        
        print(f"subscription_confirm: ERROR IntegrityError user={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref} error={str(e)}")
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
