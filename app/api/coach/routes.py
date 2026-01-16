from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import json
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
import psycopg2
from app.core.database import get_db
from app.core.security import require_role
from app.api.coach.students import router as students_router


router = APIRouter(prefix="/coach", tags=["coach"])
router.include_router(students_router)

# Predefined service tags (for future frontend use)
PREDEFINED_SERVICE_TAGS = [
    "7/24 Chat",
    "Form Analysis",
    "Nutrition Plan",
    "Personalized Workout",
    "Video Call",
    "1:1 Training",
    "Weekly Check-in",
    "Supplement Guidance",
    "Mobility/Stretching",
    "Progress Tracking"
]


def _fetchone_id(row):
    """tuple veya dict fetchone() uyumlu id okuyucu"""
    if row is None:
        return None
    if isinstance(row, dict):
        if "id" in row:
            return row["id"]
        return next(iter(row.values()))
    return row[0]


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


# --------------------------------------------------
# ACTIVE PROGRAMS (READ)
# --------------------------------------------------
@router.get("/students/{student_user_id}/active-programs")
def get_active_programs(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # student ownership check
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # workout program
    cur.execute(
        """
        SELECT id, client_user_id, title, is_active, created_at, updated_at
        FROM workout_programs
        WHERE client_user_id=%s AND is_active=TRUE
        ORDER BY id DESC
        LIMIT 1
        """,
        (student_user_id,),
    )
    workout_program = cur.fetchone()

    workout_days = []
    workout_exercises = []

    if workout_program:
        program_id = workout_program["id"]
        cur.execute(
            """
            SELECT id, workout_program_id, day_of_week, order_index, created_at, updated_at
            FROM workout_days
            WHERE workout_program_id=%s
            ORDER BY order_index ASC, id ASC
            """,
            (program_id,),
        )
        workout_days = cur.fetchall()

        cur.execute(
            """
            SELECT
                e.id, e.workout_day_id, e.exercise_name, e.sets, e.reps, e.notes, e.order_index,
                e.created_at, e.updated_at
            FROM workout_exercises e
            JOIN workout_days d ON d.id = e.workout_day_id
            WHERE d.workout_program_id=%s
            ORDER BY d.order_index ASC, e.order_index ASC, e.id ASC
            """,
            (program_id,),
        )
        workout_exercises = cur.fetchall()

    # nutrition program
    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, title, is_active, created_at, updated_at
        FROM nutrition_programs
        WHERE client_user_id=%s AND is_active=TRUE
        ORDER BY id DESC
        LIMIT 1
        """,
        (student_user_id,),
    )
    nutrition_program = cur.fetchone()

    meals = []
    if nutrition_program:
        nutrition_program_id = nutrition_program["id"]
        cur.execute(
            """
            SELECT id, nutrition_program_id, meal_type, content, order_index, created_at, updated_at
            FROM nutrition_meals
            WHERE nutrition_program_id=%s
            ORDER BY order_index ASC, id ASC
            """,
            (nutrition_program_id,),
        )
        meals = cur.fetchall()

    return {
        "workout_program": workout_program,
        "workout_days": workout_days,
        "workout_exercises": workout_exercises,
        "nutrition_program": nutrition_program,
        "meals": meals,
    }


# --------------------------------------------------
# WORKOUT PROGRAM SAVE
# --------------------------------------------------
def _flatten_day_to_exercises(day_data: dict) -> list:
    """
    Flatten a day payload (new format) into a list of exercise dicts for workout_exercises table.
    Handles warmup items and block items (including supersets).
    Returns list of {name, sets, reps, notes} dicts in order.
    """
    exercises = []
    
    # Warmup items first
    warmup = day_data.get("warmup", {}) or {}
    warmup_items = warmup.get("items", []) or []
    for item in warmup_items:
        if isinstance(item, dict):
            exercises.append({
                "name": item.get("name") or "",
                "sets": item.get("sets"),
                "reps": item.get("reps") or "",
                "notes": item.get("notes") or "",
            })
    
    # Block items
    blocks = day_data.get("blocks", []) or []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_items = block.get("items", []) or []
        for item in block_items:
            if not isinstance(item, dict):
                continue
            
            item_type = item.get("type", "exercise")
            
            if item_type == "exercise":
                exercises.append({
                    "name": item.get("name") or "",
                    "sets": item.get("sets"),
                    "reps": item.get("reps") or "",
                    "notes": item.get("notes") or "",
                })
            elif item_type == "superset":
                # Flatten superset items
                superset_items = item.get("items", []) or []
                for ss_item in superset_items:
                    if isinstance(ss_item, dict):
                        notes = ss_item.get("notes") or ""
                        # Optionally prefix with [SUPERSET] if notes exist
                        if notes:
                            notes = f"[SUPERSET] {notes}"
                        exercises.append({
                            "name": ss_item.get("name") or "",
                            "sets": ss_item.get("sets"),
                            "reps": ss_item.get("reps") or "",
                            "notes": notes,
                        })
    
    return exercises


@router.post("/students/{student_user_id}/workout-programs")
def save_workout_program(
    student_user_id: int,
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    try:
        # Create program as DRAFT (is_active=false)
        # Do NOT deactivate existing active program - that happens only on "Assign Program"
        cur.execute(
            """
            INSERT INTO workout_programs (client_user_id, coach_user_id, title, is_active)
            VALUES (%s, %s, %s, FALSE)
            RETURNING id
            """,
            (student_user_id, coach_id, "Coach Workout Program"),
        )
        program_id = _fetchone_id(cur.fetchone())

        week = payload.get("week", {}) or {}
        day_order = 1

        for day_key, day_value in week.items():
            if not day_value:
                continue

            # Detect format: old (array) vs new (object)
            is_old_format = isinstance(day_value, list)
            is_new_format = isinstance(day_value, dict)

            if not (is_old_format or is_new_format):
                continue

            # Prepare day_payload and exercises list
            day_payload_json = None
            exercises_to_insert = []

            if is_new_format:
                # New format: save day_payload JSONB
                day_payload_json = json.dumps(day_value)
                # Flatten to exercises for compatibility
                exercises_to_insert = _flatten_day_to_exercises(day_value)
            else:
                # Old format: array of exercises
                exercises_to_insert = day_value
                # Optionally generate minimal day_payload for backward compatibility
                # (We'll leave it NULL to maintain old behavior)

            # Insert workout_day
            cur.execute(
                """
                INSERT INTO workout_days (workout_program_id, day_of_week, order_index, day_payload)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (program_id, day_key, day_order, day_payload_json),
            )
            workout_day_id = _fetchone_id(cur.fetchone())

            # Insert exercises (for both old and new format)
            for ex_order, ex in enumerate(exercises_to_insert, start=1):
                if isinstance(ex, dict):
                    cur.execute(
                        """
                        INSERT INTO workout_exercises
                        (workout_day_id, exercise_name, sets, reps, notes, order_index)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            workout_day_id,
                            ex.get("name") or "",
                            ex.get("sets"),
                            ex.get("reps") or "",
                            ex.get("notes") or "",
                            ex_order,
                        ),
                    )

            day_order += 1

        db.commit()
        return {"ok": True, "program_id": program_id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving workout program: {str(e)}")


@router.get("/students/{student_user_id}/workout-programs/latest")
def get_latest_workout_program(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Get the latest saved workout program for a student (even if draft/not active).
    Returns UI-friendly flat structure for admin panel editor.
    
    Example curl:
    curl -X GET "http://localhost:8000/coach/students/36/workout-programs/latest" \
      -H "Authorization: Bearer <coach_token>"
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # Get latest program (by created_at DESC, then id DESC)
    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, title, is_active, created_at, updated_at
        FROM workout_programs
        WHERE client_user_id = %s AND coach_user_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (student_user_id, coach_id),
    )
    program = cur.fetchone()

    if not program:
        raise HTTPException(status_code=404, detail="Workout program not found")

    program_id = program["id"]
    is_active = bool(program["is_active"])

    # Get all days for this program
    cur.execute(
        """
        SELECT id, workout_program_id, day_of_week, order_index
        FROM workout_days
        WHERE workout_program_id = %s
        ORDER BY order_index ASC, id ASC
        """,
        (program_id,),
    )
    days = cur.fetchall() or []

    # Get all exercises grouped by workout_day_id
    day_ids = [d["id"] for d in days]
    exercises_by_day_id = {}
    
    if day_ids:
        placeholders = ",".join(["%s"] * len(day_ids))
        cur.execute(
            f"""
            SELECT id, workout_day_id, exercise_name, sets, reps, notes, order_index
            FROM workout_exercises
            WHERE workout_day_id IN ({placeholders})
            ORDER BY workout_day_id ASC, order_index ASC, id ASC
            """,
            tuple(day_ids),
        )
        all_exercises = cur.fetchall() or []
        
        for ex in all_exercises:
            day_id = ex["workout_day_id"]
            if day_id not in exercises_by_day_id:
                exercises_by_day_id[day_id] = []
            exercises_by_day_id[day_id].append(ex)

    # Build week structure: {mon: [], tue: [], ...}
    week_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    week = {day: [] for day in week_days}

    # Map days to week structure
    for day in days:
        day_key = day["day_of_week"]
        if day_key not in week_days:
            continue
        
        day_id = day["id"]
        exercises = exercises_by_day_id.get(day_id, [])
        
        # Convert exercises to flat format: {name, sets, reps, notes}
        week[day_key] = [
            {
                "name": ex.get("exercise_name") or "",
                "sets": ex.get("sets"),
                "reps": ex.get("reps") or "",
                "notes": ex.get("notes") or "",
            }
            for ex in exercises
        ]

    return {
        "program_id": program_id,
        "is_active": is_active,
        "week": week
    }


@router.post("/students/{student_user_id}/workout-programs/assign")
def assign_latest_workout_program(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Assign (activate) the latest workout program for a student.
    Reuses existing "set active" mechanism from assign_workout_program endpoint.
    
    Example curl:
    curl -X POST "http://localhost:8000/coach/students/36/workout-programs/assign" \
      -H "Authorization: Bearer <coach_token>"
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    try:
        # Find latest program for this student
        cur.execute(
            """
            SELECT id, client_user_id, coach_user_id, is_active
            FROM workout_programs
            WHERE client_user_id = %s AND coach_user_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (student_user_id, coach_id),
        )
        program = cur.fetchone()

        if not program:
            raise HTTPException(status_code=404, detail="Workout program not found")

        program_id = program["id"]

        # Reuse existing "set active" logic from assign_workout_program endpoint
        # 1. Deactivate all active programs for this student
        cur.execute(
            """
            UPDATE workout_programs
            SET is_active = FALSE, updated_at = NOW()
            WHERE client_user_id = %s AND is_active = TRUE
            """,
            (student_user_id,),
        )

        # 2. Activate the latest program
        cur.execute(
            """
            UPDATE workout_programs
            SET is_active = TRUE, updated_at = NOW()
            WHERE id = %s
            """,
            (program_id,),
        )

        db.commit()
        return {"ok": True, "program_id": program_id}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error assigning workout program: {str(e)}")


@router.post("/students/{student_user_id}/workout-programs/{program_id}/assign")
def assign_workout_program(
    student_user_id: int,
    program_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Assign (activate) a workout program for a student.
    This endpoint:
    1. Deactivates all currently active programs for the student
    2. Activates the specified program
    
    The program must belong to this coach and be for this student.
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    try:
        # Verify program exists, belongs to this coach, and is for this student
        cur.execute(
            """
            SELECT id, client_user_id, coach_user_id, is_active
            FROM workout_programs
            WHERE id = %s AND client_user_id = %s AND coach_user_id = %s
            """,
            (program_id, student_user_id, coach_id),
        )
        program = cur.fetchone()
        
        if not program:
            raise HTTPException(
                status_code=404,
                detail="Workout program not found or you don't have permission to assign it"
            )

        # Transaction: deactivate all active programs for this student, then activate the specified one
        cur.execute(
            """
            UPDATE workout_programs
            SET is_active = FALSE, updated_at = NOW()
            WHERE client_user_id = %s AND is_active = TRUE
            """,
            (student_user_id,),
        )

        cur.execute(
            """
            UPDATE workout_programs
            SET is_active = TRUE, updated_at = NOW()
            WHERE id = %s
            """,
            (program_id,),
        )

        db.commit()
        return {"ok": True, "active_program_id": program_id}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error assigning workout program: {str(e)}")


# --------------------------------------------------
# NUTRITION PROGRAM SAVE (MVP)
# --------------------------------------------------
@router.post("/students/{student_user_id}/nutrition-programs")
def save_nutrition_program(
    student_user_id: int,
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor()

    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    cur.execute(
        "UPDATE nutrition_programs SET is_active=FALSE WHERE client_user_id=%s AND is_active=TRUE",
        (student_user_id,),
    )

    cur.execute(
        """
        INSERT INTO nutrition_programs (client_user_id, coach_user_id, title, is_active)
        VALUES (%s, %s, %s, TRUE)
        RETURNING id
        """,
        (student_user_id, coach_id, "Coach Nutrition Program"),
    )
    nutrition_program_id = _fetchone_id(cur.fetchone())

    week = payload.get("week", {}) or {}
    day_meals = week.get("mon") or next((week[k] for k in ["tue", "wed", "thu", "fri", "sat", "sun"] if week.get(k)), [])
    day_meals = day_meals or []

    for idx, m in enumerate(day_meals, start=1):
        meal_type = m.get("type") or "Meal"
        items = m.get("items") or []
        content = json.dumps(items)

        cur.execute(
            """
            INSERT INTO nutrition_meals (nutrition_program_id, meal_type, content, order_index)
            VALUES (%s, %s, %s, %s)
            """,
            (nutrition_program_id, meal_type, content, idx),
        )

    db.commit()
    return {"ok": True, "nutrition_program_id": nutrition_program_id}


# --------------------------------------------------
# STUDENTS FILTERS
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
                s.created_at AS purchased_at
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
        SELECT DISTINCT
            u.id AS student_id,
            u.email,
            COALESCE(o.full_name, u.email) AS full_name,
            c.goal_type,
            s.ends_at,
            EXTRACT(DAY FROM s.ends_at - NOW())::int AS days_left
        FROM subscriptions s
        JOIN users u ON u.id = s.client_user_id
        LEFT JOIN clients c ON c.user_id = u.id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        WHERE s.coach_user_id = %s
          AND s.status = 'active'
          AND s.ends_at > NOW()
        ORDER BY s.ends_at ASC
        """,
        (coach_id,),
    )
    return {"students": cur.fetchall()}



# --------------------------------------------------
# COACH PROFILE (ME)
# --------------------------------------------------
@router.get("/me/profile")
def get_my_profile(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active
        FROM coaches
        WHERE user_id = %s
        """,
        (coach_id,),
    )
    row = cur.fetchone()

    if not row:
        cur.execute(
            """
            INSERT INTO coaches (user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active)
            VALUES (%s, '', NULL, NULL, 0, 0, ARRAY[]::text[], NULL, TRUE)
            RETURNING user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active
            """,
            (coach_id,),
        )
        row = cur.fetchone()
        db.commit()

    return {"profile": row}


@router.put("/me/profile")
def update_my_profile(
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    allowed_fields = {"bio", "photo_url", "price_per_month", "specialties", "instagram", "is_active"}
    updates = {k: payload.get(k) for k in payload.keys() if k in allowed_fields}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    set_parts = []
    values = []
    for k, v in updates.items():
        set_parts.append(f"{k}=%s")
        values.append(v)

    values.append(coach_id)

    cur.execute(
        f"""
        UPDATE coaches
        SET {", ".join(set_parts)}
        WHERE user_id = %s
        RETURNING user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active
        """,
        tuple(values),
    )

    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Coach profile not found")

    db.commit()
    return {"ok": True, "profile": row}


# --------------------------------------------------
# PACKAGES (NEW)
# --------------------------------------------------
def validate_services(services: Optional[List[str]]) -> List[str]:
    """
    Validate and normalize services list.
    - If None, return empty list
    - Max 12 tags
    - Each tag max 40 chars, trimmed
    """
    if services is None:
        return []
    
    # Trim and filter empty strings
    normalized = [s.strip() for s in services if s and s.strip()]
    
    # Max 12 tags
    if len(normalized) > 12:
        raise ValueError("Maximum 12 service tags allowed")
    
    # Each tag max 40 chars
    for tag in normalized:
        if len(tag) > 40:
            raise ValueError(f"Service tag '{tag}' exceeds 40 characters")
    
    return normalized


class CoachPackageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    duration_days: int = Field(gt=0)
    price: int = Field(ge=0)
    is_active: bool = True
    services: Optional[List[str]] = Field(default=None, description="List of service tags (max 12, each max 40 chars)")
    
    @field_validator('services')
    @classmethod
    def validate_services_field(cls, v):
        return validate_services(v)


class CoachPackageUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    duration_days: Optional[int] = Field(default=None, gt=0)
    price: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    services: Optional[List[str]] = Field(default=None, description="List of service tags (max 12, each max 40 chars)")
    
    @field_validator('services')
    @classmethod
    def validate_services_field(cls, v):
        return validate_services(v)


@router.get("/packages")
def list_my_packages(db=Depends(get_db), current_user=Depends(require_role("coach"))):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            SELECT id, coach_user_id, name, description, duration_days, price, is_active, created_at, updated_at
            FROM coach_packages
            WHERE coach_user_id = %s
            ORDER BY is_active DESC, created_at DESC, id DESC
            """,
            (current_user["id"],),
        )
        return {"packages": cur.fetchall()}
    except psycopg2.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error in /coach/packages: {e.pgerror or str(e)}")


@router.post("/packages")
def create_package(body: CoachPackageCreate, db=Depends(get_db), current_user=Depends(require_role("coach"))):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            INSERT INTO coach_packages (coach_user_id, name, description, duration_days, price, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, coach_user_id, name, description, duration_days, price, is_active, created_at, updated_at
            """,
            (current_user["id"], body.name, body.description, body.duration_days, body.price, body.is_active),
        )
        row = cur.fetchone()
        db.commit()
        return {"package": row}
    except psycopg2.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error in POST /coach/packages: {e.pgerror or str(e)}")


@router.put("/packages/{package_id}")
def update_package(package_id: int, body: CoachPackageUpdate, db=Depends(get_db), current_user=Depends(require_role("coach"))):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT id FROM coach_packages WHERE id=%s AND coach_user_id=%s",
            (package_id, current_user["id"]),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Package not found")

        fields = []
        values = []

        if body.name is not None:
            fields.append("name=%s"); values.append(body.name)
        if body.description is not None:
            fields.append("description=%s"); values.append(body.description)
        if body.duration_days is not None:
            fields.append("duration_days=%s"); values.append(body.duration_days)
        if body.price is not None:
            fields.append("price=%s"); values.append(body.price)
        if body.is_active is not None:
            fields.append("is_active=%s"); values.append(body.is_active)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        values.extend([package_id, current_user["id"]])

        cur.execute(
            f"""
            UPDATE coach_packages
            SET {", ".join(fields)}
            WHERE id=%s AND coach_user_id=%s
            RETURNING id, coach_user_id, name, description, duration_days, price, is_active, created_at, updated_at
            """,
            tuple(values),
        )
        row = cur.fetchone()
        db.commit()
        return {"package": row}
    except HTTPException:
        raise
    except psycopg2.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error in PUT /coach/packages: {e.pgerror or str(e)}")