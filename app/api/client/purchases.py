from fastapi import Depends, HTTPException, status
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
from app.core.security import require_role
from app.core.database import get_db
from app.schemas.subscriptions import SubscriptionConfirmRequest, SubscriptionConfirmResponse
from .routes import router
import uuid

@router.get("/ping")
def client_ping(current_user=Depends(require_role("client"))):
    return {"ok": True, "message": "client router works"}


class CheckoutRequest(BaseModel):
    coach_package_id: int


@router.post("/checkout")
def checkout(
    request: CheckoutRequest,
    current_user=Depends(require_role("client")),
    db=Depends(get_db)
):
    client_user_id = current_user["id"]
    coach_package_id = request.coach_package_id

    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        # Get package details
        cur.execute(
            """
            SELECT
                id,
                coach_user_id,
                name,
                description,
                duration_days,
                price,
                is_active
            FROM coach_packages
            WHERE id = %s AND is_active = TRUE
            """,
            (coach_package_id,)
        )

        package = cur.fetchone()
        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found or inactive"
            )

        coach_user_id = package["coach_user_id"]
        plan_name = package["name"]
        duration_days = package["duration_days"]
        price = package["price"]

        # Check for existing active subscription
        cur.execute(
            """
            SELECT id, coach_user_id, status, ends_at
            FROM subscriptions
            WHERE client_user_id = %s
              AND status = 'active'
              AND (ends_at IS NULL OR ends_at > NOW())
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (client_user_id,)
        )
        existing_sub = cur.fetchone()

        # Policy: If same coach, deactivate old subscription
        if existing_sub and existing_sub["coach_user_id"] == coach_user_id:
            cur.execute(
                """
                UPDATE subscriptions
                SET status = 'inactive'
                WHERE id = %s
                """,
                (existing_sub["id"],)
            )

        # Calculate dates
        started_at = datetime.utcnow()
        ends_at = started_at + timedelta(days=duration_days)

        # ✅ Generate subscription_ref in backend (NOT NULL constraint)
        subscription_ref = f"checkout_{client_user_id}_{coach_package_id}_{uuid.uuid4().hex}"

        # Check if package_id column exists
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'subscriptions' AND column_name = 'package_id'
            """
        )
        has_package_id = cur.fetchone() is not None

        if has_package_id:
            cur.execute(
                """
                INSERT INTO subscriptions (
                    client_user_id,
                    coach_user_id,
                    package_id,
                    plan_name,
                    subscription_ref,
                    status,
                    started_at,
                    ends_at,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING
                    id, client_user_id, coach_user_id, package_id,
                    plan_name, subscription_ref, status, started_at, ends_at, created_at
                """,
                (
                    client_user_id,
                    coach_user_id,
                    coach_package_id,
                    plan_name,
                    subscription_ref,
                    "active",
                    started_at,
                    ends_at
                )
            )
        else:
            cur.execute(
                """
                INSERT INTO subscriptions (
                    client_user_id,
                    coach_user_id,
                    plan_name,
                    subscription_ref,
                    status,
                    started_at,
                    ends_at,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING
                    id, client_user_id, coach_user_id,
                    plan_name, subscription_ref, status, started_at, ends_at, created_at
                """,
                (
                    client_user_id,
                    coach_user_id,
                    plan_name,
                    subscription_ref,
                    "active",
                    started_at,
                    ends_at
                )
            )

        new_subscription = cur.fetchone()

        # Update or insert clients.assigned_coach_id
        cur.execute("SELECT user_id FROM clients WHERE user_id = %s", (client_user_id,))
        client_exists = cur.fetchone()

        if client_exists:
            cur.execute(
                """
                UPDATE clients
                SET assigned_coach_id = %s
                WHERE user_id = %s
                """,
                (coach_user_id, client_user_id)
            )
        else:
            cur.execute(
                """
                INSERT INTO clients (user_id, assigned_coach_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET assigned_coach_id = EXCLUDED.assigned_coach_id
                """,
                (client_user_id, coach_user_id)
            )

        db.commit()

        return {
            "ok": True,
            "subscription": {
                "id": new_subscription["id"],
                "client_user_id": new_subscription["client_user_id"],
                "coach_user_id": new_subscription["coach_user_id"],
                "plan_name": new_subscription["plan_name"],
                "subscription_ref": new_subscription.get("subscription_ref"),
                "status": new_subscription["status"],
                "started_at": new_subscription["started_at"].isoformat() if new_subscription["started_at"] else None,
                "ends_at": new_subscription["ends_at"].isoformat() if new_subscription["ends_at"] else None,
            },
            "coach_user_id": coach_user_id,
            "package": {
                "id": package["id"],
                "name": package["name"],
                "description": package.get("description"),
                "duration_days": package["duration_days"],
                "price": package["price"],
            }
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"checkout: ERROR user={client_user_id} package={coach_package_id} error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )



@router.post("/subscriptions/confirm", response_model=SubscriptionConfirmResponse)
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

        # Check if there's already a subscription for this client+coach pair
        cur.execute(
            """
            SELECT id, client_user_id, coach_user_id, plan_name, subscription_ref, status, started_at
            FROM subscriptions
            WHERE client_user_id = %s AND coach_user_id = %s
            """,
            (client_user_id, coach_user_id)
        )
        existing_coach_sub = cur.fetchone()

        if existing_coach_sub:
            # Update existing subscription instead of creating duplicate
            cur.execute(
                """
                UPDATE subscriptions
                SET plan_name = %s,
                    subscription_ref = %s,
                    status = 'active',
                    started_at = %s,
                    created_at = NOW()
                WHERE id = %s
                RETURNING id, client_user_id, coach_user_id, plan_name, subscription_ref, status, started_at
                """,
                (plan_id, subscription_ref, datetime.utcnow(), existing_coach_sub["id"])
            )
            updated_sub = cur.fetchone()
            db.commit()
            print(f"subscription_confirm: user={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref} updated=True (existing coach sub)")
            return SubscriptionConfirmResponse(
                ok=True,
                subscription={
                    "id": updated_sub["id"],
                    "client_user_id": updated_sub["client_user_id"],
                    "coach_id": str(updated_sub["coach_user_id"]),
                    "plan_id": updated_sub.get("plan_name") or plan_id,
                    "subscription_ref": updated_sub["subscription_ref"],
                    "status": updated_sub["status"],
                    "started_at": updated_sub["started_at"].isoformat() if updated_sub["started_at"] else None,
                },
                created=False
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
        db.commit()
        
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
