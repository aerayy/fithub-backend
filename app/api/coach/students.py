from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor
from datetime import datetime
from fastapi import HTTPException
from app.core.database import get_db
from app.core.security import require_role

router = APIRouter()


# --------------------------------------------------
# STUDENTS (LIST)
# --------------------------------------------------
@router.get("/students")
def get_my_students(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    cur = db.cursor()
    cur.execute(
        """
        SELECT
            u.id AS student_id,
            u.email,
            COALESCE(o.full_name, u.email) AS full_name,
            c.goal_type,
            c.activity_level,
            c.onboarding_done,
            c.created_at,

            s.plan_name,
            s.status AS subscription_status,
            s.purchased_at,
            s.started_at,
            s.ends_at,
            GREATEST(0, CEIL(EXTRACT(EPOCH FROM (s.ends_at - NOW())) / 86400))::int AS days_left
        FROM clients c
        JOIN users u ON u.id = c.user_id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        LEFT JOIN LATERAL (
            SELECT *
            FROM subscriptions
            WHERE client_user_id = u.id
              AND coach_user_id = c.assigned_coach_id
            ORDER BY purchased_at DESC NULLS LAST, id DESC
            LIMIT 1
        ) s ON TRUE
        WHERE c.assigned_coach_id = %s
        ORDER BY u.id;
        """,
        (current_user["id"],),
    )
    return {"students": cur.fetchall()}


@router.get("/students/all")
def get_all_students_from_subscriptions(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        WITH latest AS (
            SELECT DISTINCT ON (s.client_user_id)
                s.client_user_id,
                s.coach_user_id,
                s.status,
                s.started_at,
                s.ends_at,
                s.created_at AS purchased_at,
                s.plan_name
            FROM subscriptions s
            WHERE s.coach_user_id = %s
            ORDER BY s.client_user_id, s.created_at DESC
        )
        SELECT
            u.id AS student_id,
            u.email,
            COALESCE(o.full_name, u.email) AS full_name,
            c.goal_type,
            l.status,
            l.plan_name,
            l.started_at,
            l.ends_at,
            l.purchased_at,
            CASE
                WHEN l.status = 'active' AND l.ends_at > NOW() THEN TRUE
                ELSE FALSE
            END AS is_active
        FROM latest l
        JOIN users u ON u.id = l.client_user_id
        LEFT JOIN clients c ON c.user_id = u.id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        ORDER BY l.purchased_at DESC;
        """,
        (coach_id,),
    )
    return {"students": cur.fetchall()}


@router.get("/students/active")
def get_active_students_from_subscriptions(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT
            u.id AS student_id,
            u.email,
            COALESCE(o.full_name, u.email) AS full_name,
            c.goal_type,
            s.plan_name,
            s.ends_at,
            EXTRACT(DAY FROM s.ends_at - NOW())::int AS days_left
        FROM clients c
        JOIN users u ON u.id = c.user_id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        LEFT JOIN LATERAL (
            SELECT plan_name, ends_at
            FROM subscriptions
            WHERE client_user_id = u.id AND coach_user_id = %s
            ORDER BY id DESC
            LIMIT 1
        ) s ON TRUE
        WHERE c.assigned_coach_id = %s
        ORDER BY u.id
        """,
        (coach_id, coach_id),
    )
    return {"students": cur.fetchall()}


# --------------------------------------------------
# NEW PURCHASES (PENDING)  ✅
# --------------------------------------------------
@router.get("/students/new-purchases")
def get_new_purchases(
    days: int = 7,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
    """
    SELECT
        s.id AS subscription_id,                -- ✅ KRİTİK
        s.client_user_id AS student_id,
        u.email,
        COALESCE(o.full_name, u.email) AS full_name,
        c.goal_type,
        s.status,
        s.purchased_at,
        EXTRACT(DAY FROM NOW() - s.purchased_at)::int AS days_ago
    FROM subscriptions s
    JOIN users u ON u.id = s.client_user_id
    LEFT JOIN clients c ON c.user_id = u.id
    LEFT JOIN client_onboarding o ON o.user_id = u.id
    WHERE s.coach_user_id = %s
      AND s.status = 'pending'
      AND s.purchased_at >= NOW() - (%s || ' days')::interval
    ORDER BY s.purchased_at DESC
    """,
    (coach_id, days),
)


    return {"students": cur.fetchall()}


# --------------------------------------------------
# APPROVE / REJECT ✅
# --------------------------------------------------
def _has_column(cur, table: str, column: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return cur.fetchone() is not None


@router.post("/students/{student_id}/subscriptions/{subscription_id}/approve")
def approve_subscription(
    student_id: int,
    subscription_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # subscription bu coach + öğrenciye ait mi ve pending mi?
    cur.execute(
        """
        SELECT s.id, s.status, s.started_at, s.ends_at, s.package_id, cp.duration_days
        FROM subscriptions s
        LEFT JOIN coach_packages cp ON cp.id = s.package_id
        WHERE s.id = %s AND s.client_user_id = %s AND s.coach_user_id = %s
        """,
        (subscription_id, student_id, coach_id),
    )
    sub = cur.fetchone()
    if not sub:
        raise HTTPException(404, "Subscription not found")
    if sub["status"] != "pending":
        raise HTTPException(400, f"Cannot approve subscription with status={sub['status']}")

    started_at = sub["started_at"] or datetime.utcnow()
    ends_at = sub["ends_at"]

    # ends_at yoksa duration_days ile hesapla (package üzerinden)
    if ends_at is None:
        dur = sub.get("duration_days") or 30  # duration yoksa 30 gün default
        cur.execute(
            """
            UPDATE subscriptions
            SET
              status='active',
              started_at=%s,
              ends_at=%s + (%s || ' days')::interval,
              decided_at=NOW(),
              decision='approved'
            WHERE id=%s
            """,
            (started_at, started_at, dur, subscription_id),
        )
    else:
        cur.execute(
            """
            UPDATE subscriptions
            SET
              status='active',
              started_at=%s,
              decided_at=NOW(),
              decision='approved'
            WHERE id=%s
            """,
            (started_at, subscription_id),
        )

    db.commit()
    return {"ok": True}


@router.post("/students/{student_id}/subscriptions/{subscription_id}/reject")
def reject_subscription(
    student_id: int,
    subscription_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT id, status
        FROM subscriptions
        WHERE id = %s AND client_user_id = %s AND coach_user_id = %s
        """,
        (subscription_id, student_id, coach_id),
    )
    sub = cur.fetchone()
    if not sub:
        raise HTTPException(404, "Subscription not found")
    if sub["status"] != "pending":
        raise HTTPException(400, f"Cannot reject subscription with status={sub['status']}")

    cur.execute(
        """
        UPDATE subscriptions
        SET status='rejected', decided_at=NOW(), decision='rejected'
        WHERE id=%s
        """,
        (subscription_id,),
    )
    db.commit()
    return {"ok": True}


# --------------------------------------------------
# NEW PROGRAMS (unchanged)
# --------------------------------------------------
@router.get("/students/new-programs")
def get_students_with_new_programs(
    days: int = Query(7, ge=1, le=365),
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor()

    cur.execute(
        """
        WITH latest_workout AS (
            SELECT client_user_id, MAX(created_at) AS last_workout_at
            FROM workout_programs
            WHERE coach_user_id = %s
            GROUP BY client_user_id
        ),
        latest_nutrition AS (
            SELECT client_user_id, MAX(created_at) AS last_nutrition_at
            FROM nutrition_programs
            WHERE coach_user_id = %s
            GROUP BY client_user_id
        )
        SELECT
            u.id AS student_id,
            u.email,
            COALESCE(o.full_name, u.email) AS full_name,
            c.goal_type,
            c.activity_level,
            c.onboarding_done,
            c.created_at,
            lw.last_workout_at,
            ln.last_nutrition_at,
            GREATEST(
                COALESCE(lw.last_workout_at, '1970-01-01'::timestamp),
                COALESCE(ln.last_nutrition_at, '1970-01-01'::timestamp)
            ) AS last_program_at
        FROM clients c
        JOIN users u ON u.id = c.user_id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        LEFT JOIN latest_workout lw ON lw.client_user_id = u.id
        LEFT JOIN latest_nutrition ln ON ln.client_user_id = u.id
        WHERE c.assigned_coach_id = %s
          AND GREATEST(
                COALESCE(lw.last_workout_at, '1970-01-01'::timestamp),
                COALESCE(ln.last_nutrition_at, '1970-01-01'::timestamp)
          ) >= NOW() - (%s || ' days')::interval
        ORDER BY last_program_at DESC NULLS LAST, u.id DESC;
        """,
        (coach_id, coach_id, coach_id, days),
    )
    return {"students": cur.fetchall()}
