# app/api/superadmin.py
"""SuperAdmin endpoints — system-wide management for app owner."""
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
from app.core.security import require_role
from app.core.database import get_db

router = APIRouter(prefix="/superadmin", tags=["superadmin"])


@router.get("/dashboard")
def superadmin_dashboard(
    db=Depends(get_db),
    user=Depends(require_role("superadmin")),
):
    """System-wide KPIs and metrics."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Total users by role
    cur.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
    role_counts = {r["role"]: r["count"] for r in (cur.fetchall() or [])}

    # Active subscriptions
    cur.execute("""
        SELECT COUNT(*) as count FROM subscriptions
        WHERE status = 'active' AND (ends_at IS NULL OR ends_at > NOW())
    """)
    active_subs = cur.fetchone()["count"]

    # Monthly revenue (last 30 days)
    cur.execute("""
        SELECT COALESCE(SUM(cp.price), 0) as revenue
        FROM subscriptions s
        JOIN coach_packages cp ON cp.id = s.package_id
        WHERE s.status = 'active'
          AND s.started_at > NOW() - INTERVAL '30 days'
    """)
    monthly_revenue = float(cur.fetchone()["revenue"] or 0)

    # New users this week
    cur.execute("SELECT COUNT(*) as count FROM users WHERE created_at > NOW() - INTERVAL '7 days'")
    new_users_week = cur.fetchone()["count"]

    # New users this month
    cur.execute("SELECT COUNT(*) as count FROM users WHERE created_at > NOW() - INTERVAL '30 days'")
    new_users_month = cur.fetchone()["count"]

    # Canceled subscriptions last 30 days (churn)
    cur.execute("""
        SELECT COUNT(*) as count FROM subscriptions
        WHERE status = 'canceled' AND updated_at > NOW() - INTERVAL '30 days'
    """)
    canceled_month = cur.fetchone()["count"]

    # Total coaches
    cur.execute("SELECT COUNT(*) as count FROM coaches WHERE is_active = TRUE")
    active_coaches = cur.fetchone()["count"]

    # Total food items
    cur.execute("SELECT COUNT(*) as count FROM food_items")
    total_foods = cur.fetchone()["count"]

    # Total exercises
    cur.execute("SELECT COUNT(*) as count FROM exercise_library")
    total_exercises = cur.fetchone()["count"]

    return {
        "users": {
            "total_clients": role_counts.get("client", 0),
            "total_coaches": role_counts.get("coach", 0),
            "total_superadmin": role_counts.get("superadmin", 0),
            "new_this_week": new_users_week,
            "new_this_month": new_users_month,
        },
        "subscriptions": {
            "active": active_subs,
            "canceled_this_month": canceled_month,
            "monthly_revenue": monthly_revenue,
        },
        "content": {
            "active_coaches": active_coaches,
            "total_foods": total_foods,
            "total_exercises": total_exercises,
        },
    }


@router.get("/coaches")
def list_all_coaches(
    db=Depends(get_db),
    user=Depends(require_role("superadmin")),
):
    """List all coaches with their stats."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT
            c.user_id,
            u.full_name,
            u.email,
            COALESCE(c.photo_url, u.profile_photo_url) AS photo_url,
            c.bio,
            c.rating,
            c.rating_count,
            c.is_active,
            c.specialties,
            u.created_at,
            (SELECT COUNT(*) FROM clients cl WHERE cl.assigned_coach_id = c.user_id) AS student_count,
            (SELECT COUNT(*) FROM subscriptions s WHERE s.coach_user_id = c.user_id AND s.status = 'active') AS active_sub_count,
            (SELECT COALESCE(SUM(cp.price), 0) FROM subscriptions s
             JOIN coach_packages cp ON cp.id = s.package_id
             WHERE s.coach_user_id = c.user_id AND s.status = 'active') AS revenue
        FROM coaches c
        JOIN users u ON u.id = c.user_id
        ORDER BY c.is_active DESC, student_count DESC, u.created_at DESC
    """)
    coaches = cur.fetchall() or []
    for c in coaches:
        if c.get("revenue") is not None:
            c["revenue"] = float(c["revenue"])
    return {"coaches": coaches}


@router.patch("/coaches/{coach_user_id}/toggle-active")
def toggle_coach_active(
    coach_user_id: int,
    db=Depends(get_db),
    user=Depends(require_role("superadmin")),
):
    """Activate or deactivate a coach."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "UPDATE coaches SET is_active = NOT is_active WHERE user_id = %s RETURNING user_id, is_active",
        (coach_user_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Koç bulunamadı")
    db.commit()
    return {"ok": True, "coach_user_id": row["user_id"], "is_active": row["is_active"]}


@router.get("/students")
def list_all_students(
    db=Depends(get_db),
    user=Depends(require_role("superadmin")),
):
    """List all students with subscription info."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT
            u.id AS user_id,
            u.full_name,
            u.email,
            u.profile_photo_url,
            u.created_at,
            c.assigned_coach_id,
            c.onboarding_done,
            c.goal_type,
            coach_u.full_name AS coach_name,
            s.status AS sub_status,
            s.plan_name,
            s.ends_at
        FROM users u
        JOIN clients c ON c.user_id = u.id
        LEFT JOIN users coach_u ON coach_u.id = c.assigned_coach_id
        LEFT JOIN LATERAL (
            SELECT status, plan_name, ends_at
            FROM subscriptions
            WHERE client_user_id = u.id
            ORDER BY created_at DESC LIMIT 1
        ) s ON TRUE
        WHERE u.role = 'client'
        ORDER BY u.created_at DESC
    """)
    return {"students": cur.fetchall() or []}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db=Depends(get_db),
    user=Depends(require_role("superadmin")),
):
    """Delete a user account completely."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Check user exists
    cur.execute("SELECT id, role, email FROM users WHERE id = %s", (user_id,))
    target = cur.fetchone()
    if not target:
        raise HTTPException(404, "Kullanıcı bulunamadı")

    # Prevent deleting self
    if target["id"] == user["id"]:
        raise HTTPException(400, "Kendi hesabınızı silemezsiniz")

    # Delete cascading data
    cur.execute("DELETE FROM body_measurements WHERE client_user_id = %s", (user_id,))
    cur.execute("DELETE FROM fcm_tokens WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE client_user_id = %s OR coach_user_id = %s)", (user_id, user_id))
    cur.execute("DELETE FROM conversations WHERE client_user_id = %s OR coach_user_id = %s", (user_id, user_id))
    cur.execute("DELETE FROM nutrition_meals WHERE nutrition_program_id IN (SELECT id FROM nutrition_programs WHERE client_user_id = %s)", (user_id,))
    cur.execute("DELETE FROM nutrition_programs WHERE client_user_id = %s", (user_id,))
    cur.execute("DELETE FROM workout_exercises WHERE workout_day_id IN (SELECT id FROM workout_days WHERE workout_program_id IN (SELECT id FROM workout_programs WHERE client_user_id = %s))", (user_id,))
    cur.execute("DELETE FROM workout_days WHERE workout_program_id IN (SELECT id FROM workout_programs WHERE client_user_id = %s)", (user_id,))
    cur.execute("DELETE FROM workout_programs WHERE client_user_id = %s", (user_id,))
    cur.execute("DELETE FROM subscriptions WHERE client_user_id = %s OR coach_user_id = %s", (user_id, user_id))
    cur.execute("DELETE FROM client_onboarding WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM clients WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM coaches WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))

    db.commit()
    return {"ok": True, "deleted_user_id": user_id, "email": target["email"]}


@router.get("/subscriptions")
def list_all_subscriptions(
    db=Depends(get_db),
    user=Depends(require_role("superadmin")),
):
    """List all subscriptions."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT
            s.id,
            s.client_user_id,
            cu.full_name AS client_name,
            s.coach_user_id,
            cou.full_name AS coach_name,
            s.plan_name,
            s.status,
            s.started_at,
            s.ends_at,
            cp.price
        FROM subscriptions s
        JOIN users cu ON cu.id = s.client_user_id
        JOIN users cou ON cou.id = s.coach_user_id
        LEFT JOIN coach_packages cp ON cp.id = s.package_id
        ORDER BY s.created_at DESC
        LIMIT 100
    """)
    rows = cur.fetchall() or []
    for r in rows:
        if r.get("price") is not None:
            r["price"] = float(r["price"])
        for f in ["started_at", "ends_at"]:
            if r.get(f) and hasattr(r[f], "isoformat"):
                r[f] = r[f].isoformat()
    return {"subscriptions": rows}
