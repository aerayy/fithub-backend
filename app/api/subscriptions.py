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
    Idempotent: if subscription already exists for this client_user_id and package_id,
    returns existing record instead of creating duplicate.
    
    Validates:
    - coach_packages row exists with id = planId
    - coach_user_id in coach_packages matches coachId
    - package is active (is_active = true)
    """
    print(f"[SUBSCRIPTION_CONFIRM] Endpoint hit: path=/subscriptions/confirm")  # Log at start
    
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
    print(f"[SUBSCRIPTION_CONFIRM] INPUT: client_user_id={client_user_id} coachId={coach_id} planId={plan_id} subscriptionId={subscription_ref}")
    
    cur = db.cursor(cursor_factory=RealDictCursor)
    
    # Check if subscription_ref/external_subscription_id column exists for idempotency
    def _has_column(cur, table: str, column: str) -> bool:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
            """,
            (table, column),
        )
        return cur.fetchone() is not None
    
    # Check for external_subscription_id or subscription_ref column for storing subscriptionId
    has_external_id_column = _has_column(cur, "subscriptions", "external_subscription_id")
    has_subscription_ref_column = _has_column(cur, "subscriptions", "subscription_ref")
    
    # Early idempotency check by subscriptionId if column exists
    if has_external_id_column or has_subscription_ref_column:
        idempotency_column = "external_subscription_id" if has_external_id_column else "subscription_ref"
        cur.execute(
            f"""
            SELECT id, client_user_id, coach_user_id, package_id, plan_name, status, started_at, ends_at, purchased_at
            FROM subscriptions
            WHERE client_user_id = %s AND {idempotency_column} = %s
            """,
            (client_user_id, subscription_ref)
        )
        existing_by_ref = cur.fetchone()
        if existing_by_ref:
            print(f"[SUBSCRIPTION_CONFIRM] IDEMPOTENCY: Found existing subscription by {idempotency_column}={subscription_ref} id={existing_by_ref['id']}")
            return SubscriptionConfirmResponse(
                ok=True,
                subscription={
                    "id": existing_by_ref["id"],
                    "client_user_id": existing_by_ref["client_user_id"],
                    "coach_id": str(existing_by_ref["coach_user_id"]),
                    "package_id": existing_by_ref.get("package_id"),
                    "plan_id": existing_by_ref.get("plan_name") or plan_id,
                    "subscription_ref": subscription_ref,
                    "status": existing_by_ref["status"],
                    "started_at": existing_by_ref["started_at"].isoformat() if existing_by_ref["started_at"] else None,
                    "ends_at": existing_by_ref["ends_at"].isoformat() if existing_by_ref["ends_at"] else None,
                    "purchased_at": existing_by_ref["purchased_at"].isoformat() if existing_by_ref["purchased_at"] else None,
                },
                created=False
            )
    
    # Create new subscription
    try:
        # Parse coachId: support both "coach_18" and "18" formats
        coach_user_id = None
        if coach_id.startswith("coach_"):
            try:
                coach_user_id = int(coach_id.replace("coach_", ""))
                print(f"[SUBSCRIPTION_CONFIRM] Parsed coachId '{coach_id}' -> {coach_user_id}")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid coach_id format: {coach_id}. Expected 'coach_18' or '18'"
                )
        else:
            try:
                coach_user_id = int(coach_id)
                print(f"[SUBSCRIPTION_CONFIRM] Parsed coachId '{coach_id}' -> {coach_user_id}")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid coach_id: {coach_id}. Expected numeric ID or 'coach_18' format"
                )
        
        # Parse planId: must be integer (package_id)
        try:
            package_id_int = int(plan_id)
            print(f"[SUBSCRIPTION_CONFIRM] Parsed planId '{plan_id}' -> package_id={package_id_int}")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid planId: {plan_id}. Must be a numeric package_id"
            )
        
        # Validate package exists, is active, and belongs to coach
        cur.execute(
            """
            SELECT id, name, duration_days, coach_user_id, is_active
            FROM coach_packages
            WHERE id = %s
            """,
            (package_id_int,)
        )
        package_info = cur.fetchone()
        
        if not package_info:
            print(f"[SUBSCRIPTION_CONFIRM] VALIDATION FAILED: Package {package_id_int} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Package {package_id_int} not found"
            )
        
        # Validate package is active
        if not package_info.get("is_active"):
            print(f"[SUBSCRIPTION_CONFIRM] VALIDATION FAILED: Package {package_id_int} is not active")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Package {package_id_int} is not active"
            )
        
        # Validate package belongs to coach
        if package_info["coach_user_id"] != coach_user_id:
            print(f"[SUBSCRIPTION_CONFIRM] VALIDATION FAILED: Package {package_id_int} (coach_user_id={package_info['coach_user_id']}) does not belong to coach {coach_user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Package {package_id_int} does not belong to coach {coach_user_id}"
            )
        
        print(f"[SUBSCRIPTION_CONFIRM] VALIDATION PASSED: Package {package_id_int} exists, is active, and belongs to coach {coach_user_id}")
        
        # Extract package details
        package_id = package_id_int
        plan_name = package_info["name"]
        duration_days = package_info.get("duration_days")
        actual_coach_user_id = package_info["coach_user_id"]  # Use from DB, not parsed value
        
        # Calculate ends_at if duration_days exists
        now = datetime.utcnow()
        started_at = now
        ends_at = None
        if duration_days:
            ends_at = started_at + timedelta(days=duration_days)
            print(f"[SUBSCRIPTION_CONFIRM] Calculated ends_at: {ends_at} (duration_days={duration_days})")
        else:
            print(f"[SUBSCRIPTION_CONFIRM] No duration_days, ends_at will be NULL")
        
        # Check idempotency: existing active subscription for same client + package
        cur.execute(
            """
            SELECT id, client_user_id, coach_user_id, package_id, plan_name, status, started_at, ends_at, purchased_at
            FROM subscriptions
            WHERE client_user_id = %s AND package_id = %s AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (client_user_id, package_id)
        )
        existing_active_subscription = cur.fetchone()
        
        if existing_active_subscription:
            print(f"[SUBSCRIPTION_CONFIRM] IDEMPOTENCY: Found existing active subscription id={existing_active_subscription['id']} for client={client_user_id} package={package_id}")
            return SubscriptionConfirmResponse(
                ok=True,
                subscription={
                    "id": existing_active_subscription["id"],
                    "client_user_id": existing_active_subscription["client_user_id"],
                    "coach_id": str(existing_active_subscription["coach_user_id"]),
                    "package_id": existing_active_subscription.get("package_id"),
                    "plan_id": existing_active_subscription.get("plan_name") or plan_id,
                    "subscription_ref": subscription_ref,
                    "status": existing_active_subscription["status"],
                    "started_at": existing_active_subscription["started_at"].isoformat() if existing_active_subscription["started_at"] else None,
                    "ends_at": existing_active_subscription["ends_at"].isoformat() if existing_active_subscription["ends_at"] else None,
                    "purchased_at": existing_active_subscription["purchased_at"].isoformat() if existing_active_subscription["purchased_at"] else None,
                },
                created=False
            )
        
        # Build INSERT query dynamically based on available columns
        columns = ["client_user_id", "coach_user_id", "package_id", "plan_name", "status", "purchased_at", "started_at", "ends_at", "created_at", "updated_at"]
        values = [client_user_id, actual_coach_user_id, package_id, plan_name, "active", now, started_at, ends_at, now, now]
        placeholders = ["%s"] * len(values)
        
        print(f"[SUBSCRIPTION_CONFIRM] INSERT VALUES: client_user_id={client_user_id}, coach_user_id={actual_coach_user_id}, package_id={package_id}, plan_name='{plan_name}', status='active'")
        
        # Add external_subscription_id or subscription_ref if column exists (for storing subscriptionId)
        if has_external_id_column:
            columns.append("external_subscription_id")
            values.append(subscription_ref)
            placeholders.append("%s")
            print(f"[SUBSCRIPTION_CONFIRM] Storing subscriptionId in external_subscription_id column")
        elif has_subscription_ref_column:
            columns.append("subscription_ref")
            values.append(subscription_ref)
            placeholders.append("%s")
            print(f"[SUBSCRIPTION_CONFIRM] Storing subscriptionId in subscription_ref column")
        else:
            print(f"[SUBSCRIPTION_CONFIRM] WARNING: No external_subscription_id or subscription_ref column found. subscriptionId={subscription_ref} will not be stored but will be returned in response.")
        
        # Build RETURNING clause
        returning_cols = ["id", "client_user_id", "coach_user_id", "package_id", "plan_name", "status", "started_at", "ends_at", "purchased_at"]
        
        # Insert subscription
        insert_query = f"""
            INSERT INTO subscriptions ({", ".join(columns)})
            VALUES ({", ".join(placeholders)})
            RETURNING {", ".join(returning_cols)}
        """
        
        cur.execute(insert_query, tuple(values))
        
        new_subscription = cur.fetchone()
        db.commit()  # Explicit commit after insert
        
        print(f"[SUBSCRIPTION_CONFIRM] SUCCESS: Created subscription id={new_subscription['id']} for client={client_user_id} coach={actual_coach_user_id} package={package_id} ref={subscription_ref}")
        
        return SubscriptionConfirmResponse(
            ok=True,
            subscription={
                "id": new_subscription["id"],
                "client_user_id": new_subscription["client_user_id"],
                "coach_id": str(new_subscription["coach_user_id"]),
                "package_id": new_subscription.get("package_id"),
                "plan_id": new_subscription.get("plan_name") or plan_id,
                "subscription_ref": subscription_ref,  # Return the provided ref
                "status": new_subscription["status"],
                "started_at": new_subscription["started_at"].isoformat() if new_subscription["started_at"] else None,
                "ends_at": new_subscription["ends_at"].isoformat() if new_subscription["ends_at"] else None,
                "purchased_at": new_subscription["purchased_at"].isoformat() if new_subscription["purchased_at"] else None,
            },
            created=True
        )
        
    except IntegrityError as e:
        db.rollback()
        print(f"[SUBSCRIPTION_CONFIRM] IntegrityError caught: {str(e)}")
        # Handle unique constraint violation (race condition)
        # Try to find existing subscription by package_id (idempotency)
        try:
            # Try to get package_id from planId
            package_id_int = int(plan_id)
            cur.execute(
                """
                SELECT id, client_user_id, coach_user_id, package_id, plan_name, status, started_at, ends_at, purchased_at
                FROM subscriptions
                WHERE client_user_id = %s AND package_id = %s AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (client_user_id, package_id_int)
            )
            existing_subscription = cur.fetchone()
            if existing_subscription:
                print(f"[SUBSCRIPTION_CONFIRM] RACE CONDITION: Found existing subscription id={existing_subscription['id']}")
                return SubscriptionConfirmResponse(
                    ok=True,
                    subscription={
                        "id": existing_subscription["id"],
                        "client_user_id": existing_subscription["client_user_id"],
                        "coach_id": str(existing_subscription["coach_user_id"]),
                        "package_id": existing_subscription.get("package_id"),
                        "plan_id": existing_subscription.get("plan_name") or plan_id,
                        "subscription_ref": subscription_ref,
                        "status": existing_subscription["status"],
                        "started_at": existing_subscription["started_at"].isoformat() if existing_subscription["started_at"] else None,
                        "ends_at": existing_subscription["ends_at"].isoformat() if existing_subscription["ends_at"] else None,
                        "purchased_at": existing_subscription["purchased_at"].isoformat() if existing_subscription["purchased_at"] else None,
                    },
                    created=False
                )
        except (ValueError, Exception) as lookup_error:
            print(f"[SUBSCRIPTION_CONFIRM] Could not lookup existing subscription after IntegrityError: {lookup_error}")
        
        print(f"[SUBSCRIPTION_CONFIRM] ERROR IntegrityError: client={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref} error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create subscription: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        print(f"[SUBSCRIPTION_CONFIRM] ERROR: client={client_user_id} coach={coach_id} plan={plan_id} ref={subscription_ref} error={str(e)}")
        import traceback
        print(f"[SUBSCRIPTION_CONFIRM] TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
