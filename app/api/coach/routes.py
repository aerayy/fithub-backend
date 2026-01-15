from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import json

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
@router.post("/students/{student_user_id}/workout-programs")
def save_workout_program(
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
        "UPDATE workout_programs SET is_active=FALSE WHERE client_user_id=%s AND is_active=TRUE",
        (student_user_id,),
    )

    cur.execute(
        """
        INSERT INTO workout_programs (client_user_id, coach_user_id, title, is_active)
        VALUES (%s, %s, %s, TRUE)
        RETURNING id
        """,
        (student_user_id, coach_id, "Coach Workout Program"),
    )
    program_id = _fetchone_id(cur.fetchone())

    week = payload.get("week", {}) or {}
    day_order = 1

    for day_key, exercises in week.items():
        if not exercises:
            continue

        cur.execute(
            """
            INSERT INTO workout_days (workout_program_id, day_of_week, order_index)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (program_id, day_key, day_order),
        )
        workout_day_id = _fetchone_id(cur.fetchone())

        for ex_order, ex in enumerate(exercises, start=1):
            cur.execute(
                """
                INSERT INTO workout_exercises
                (workout_day_id, exercise_name, sets, reps, notes, order_index)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    workout_day_id,
                    ex.get("name"),
                    ex.get("sets"),
                    ex.get("reps"),
                    ex.get("notes"),
                    ex_order,
                ),
            )

        day_order += 1

    db.commit()
    return {"ok": True, "program_id": program_id}


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
def list_my_packages(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT id, coach_user_id, name, description, duration_days, price, is_active, services, created_at, updated_at
        FROM coach_packages
        WHERE coach_user_id = %s
        ORDER BY is_active DESC, created_at DESC, id DESC
        """,
        (current_user["id"],),
    )
    return {"packages": cur.fetchall()}


@router.post("/packages")
def create_package(
    body: CoachPackageCreate,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    cur = db.cursor(cursor_factory=RealDictCursor)
    
    # Normalize services: None -> empty array
    services_list = body.services if body.services is not None else []
    
    cur.execute(
        """
        INSERT INTO coach_packages (coach_user_id, name, description, duration_days, price, is_active, services)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, coach_user_id, name, description, duration_days, price, is_active, services, created_at, updated_at
        """,
        (current_user["id"], body.name, body.description, body.duration_days, body.price, body.is_active, services_list),
    )
    row = cur.fetchone()
    db.commit()
    return {"package": row}


@router.put("/packages/{package_id}")
def update_package(
    package_id: int,
    body: CoachPackageUpdate,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT id FROM coach_packages WHERE id=%s AND coach_user_id=%s",
        (package_id, current_user["id"]),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Package not found")

    fields = []
    values = []

    if body.name is not None:
        fields.append("name=%s")
        values.append(body.name)
    if body.description is not None:
        fields.append("description=%s")
        values.append(body.description)
    if body.duration_days is not None:
        fields.append("duration_days=%s")
        values.append(body.duration_days)
    if body.price is not None:
        fields.append("price=%s")
        values.append(body.price)
    if body.is_active is not None:
        fields.append("is_active=%s")
        values.append(body.is_active)
    if body.services is not None:
        fields.append("services=%s")
        values.append(body.services)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.extend([package_id, current_user["id"]])

    cur.execute(
        f"""
        UPDATE coach_packages
        SET {", ".join(fields)}
        WHERE id=%s AND coach_user_id=%s
        RETURNING id, coach_user_id, name, description, duration_days, price, is_active, services, created_at, updated_at
        """,
        tuple(values),
    )
    row = cur.fetchone()
    db.commit()
    return {"package": row}

