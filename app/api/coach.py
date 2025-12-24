from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.security import require_role
import json
from fastapi import HTTPException
from psycopg2.extras import RealDictCursor
from fastapi import Query


router = APIRouter(prefix="/coach", tags=["coach"])


def _fetchone_id(row):
    """tuple veya dict fetchone() uyumlu id okuyucu"""
    if row is None:
        return None
    if isinstance(row, dict):
        if "id" in row:
            return row["id"]
        return next(iter(row.values()))
    return row[0]


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
# GET ACTIVE PROGRAMS (READ)
# --------------------------------------------------
@router.get("/students/{student_user_id}/active-programs")
def get_active_programs(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # 1) Öğrenci bu koça mı ait?
    cur.execute(
        """
        SELECT 1
        FROM clients
        WHERE user_id = %s AND assigned_coach_id = %s
        """,
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # ----------------------------
    # 2) Aktif workout programı
    # ----------------------------
    cur.execute(
        """
        SELECT id, client_user_id, title, is_active, created_at, updated_at
        FROM workout_programs
        WHERE client_user_id = %s AND is_active = TRUE
        ORDER BY id DESC
        LIMIT 1
        """,
        (student_user_id,),
    )
    workout_program = cur.fetchone()

    workout_days = []
    workout_exercises = []

    if workout_program:
        program_id = workout_program["id"] if isinstance(workout_program, dict) else workout_program[0]

        # workout_days
        cur.execute(
            """
            SELECT id, workout_program_id, day_of_week, order_index, created_at, updated_at
            FROM workout_days
            WHERE workout_program_id = %s
            ORDER BY order_index ASC, id ASC
            """,
            (program_id,),
        )
        workout_days = cur.fetchall()

        # workout_exercises
        cur.execute(
            """
            SELECT
                e.id,
                e.workout_day_id,
                e.exercise_name,
                e.sets,
                e.reps,
                e.notes,
                e.order_index,
                e.created_at,
                e.updated_at
            FROM workout_exercises e
            JOIN workout_days d ON d.id = e.workout_day_id
            WHERE d.workout_program_id = %s
            ORDER BY d.order_index ASC, e.order_index ASC, e.id ASC
            """,
            (program_id,),
        )
        workout_exercises = cur.fetchall()

    # ----------------------------
    # 3) Aktif nutrition programı
    # ----------------------------
    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, title, is_active, created_at, updated_at
        FROM nutrition_programs
        WHERE client_user_id = %s AND is_active = TRUE
        ORDER BY id DESC
        LIMIT 1
        """,
        (student_user_id,),
    )
    nutrition_program = cur.fetchone()

    meals = []
    if nutrition_program:
        nutrition_program_id = (
            nutrition_program["id"] if isinstance(nutrition_program, dict) else nutrition_program[0]
        )

        cur.execute(
            """
            SELECT id, nutrition_program_id, meal_type, content, order_index, created_at, updated_at
            FROM nutrition_meals
            WHERE nutrition_program_id = %s
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

    # 1) Öğrenci koça mı ait
    cur.execute(
        """
        SELECT 1
        FROM clients
        WHERE user_id = %s AND assigned_coach_id = %s
        """,
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # 2) Eski aktif programı kapat
    cur.execute(
        """
        UPDATE workout_programs
        SET is_active = FALSE
        WHERE client_user_id = %s AND is_active = TRUE
        """,
        (student_user_id,),
    )

    # 3) Yeni workout program oluştur
    cur.execute(
    """
    INSERT INTO workout_programs (client_user_id, coach_user_id, title, is_active)
    VALUES (%s, %s, %s, TRUE)
    RETURNING id
    """,
    (student_user_id, coach_id, "Coach Workout Program"),
)

    program_row = cur.fetchone()
    program_id = _fetchone_id(program_row)

    week = payload.get("week", {}) or {}

    day_order = 1
    for day_key, exercises in week.items():
        if not exercises:
            continue

        # 4) workout_days → programa bağlı
        cur.execute(
            """
            INSERT INTO workout_days
            (workout_program_id, day_of_week, order_index)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (program_id, day_key, day_order),
        )
        workout_day_row = cur.fetchone()
        workout_day_id = _fetchone_id(workout_day_row)

        # 5) workout_exercises → SADECE workout_day_id
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



@router.post("/students/{student_user_id}/nutrition-programs")
def save_nutrition_program(
    student_user_id: int,
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor()

    # 1) Öğrenci bu koça mı ait?
    cur.execute(
        """
        SELECT 1
        FROM clients
        WHERE user_id = %s AND assigned_coach_id = %s
        """,
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # 2) Eski aktif nutrition programı pasifle
    cur.execute(
        """
        UPDATE nutrition_programs
        SET is_active = FALSE
        WHERE client_user_id = %s AND is_active = TRUE
        """,
        (student_user_id,),
    )

    # 3) Yeni nutrition program oluştur
    cur.execute(
        """
        INSERT INTO nutrition_programs (client_user_id, coach_user_id, title, is_active)
        VALUES (%s, %s, %s, TRUE)
        RETURNING id
        """,
        (student_user_id, coach_id, "Coach Nutrition Program"),
    )
    row = cur.fetchone()
    nutrition_program_id = row["id"] if isinstance(row, dict) else row[0]

    # 4) Payload week yapısı: { week: { mon:[{type,items}], tue:... } }
    week = payload.get("week", {}) or {}

    # MVP: tüm günler aynı olsun diye "mon"u baz alıyoruz.
    # mon yoksa ilk dolu günü al.
    day_meals = week.get("mon")
    if not day_meals:
        for k in ["tue", "wed", "thu", "fri", "sat", "sun"]:
            if week.get(k):
                day_meals = week.get(k)
                break
    day_meals = day_meals or []

    # 5) meals yaz (order_index ile)
    # content: items list'ini JSON string olarak saklıyoruz (UI zaten parse ediyor)
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
            ) AS last_program_at,
            CASE
                WHEN COALESCE(lw.last_workout_at, '1970-01-01'::timestamp)
                   >= COALESCE(ln.last_nutrition_at, '1970-01-01'::timestamp)
                THEN 'workout'
                ELSE 'nutrition'
            END AS last_program_type

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


@router.get("/students/new-purchases")
def get_new_purchases(
    days: int = Query(7, ge=1, le=365),
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
            s.created_at AS purchased_at,
            EXTRACT(DAY FROM NOW() - s.created_at)::int AS days_ago
        FROM subscriptions s
        JOIN users u ON u.id = s.client_user_id
        LEFT JOIN clients c ON c.user_id = u.id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        WHERE s.coach_user_id = %s
          AND s.created_at >= NOW() - (%s || ' days')::interval
        ORDER BY s.created_at DESC
        """,
        (coach_id, days),
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
        SELECT
            user_id,
            bio,
            photo_url,
            price_per_month,
            rating,
            rating_count,
            specialties,
            instagram,
            is_active
        FROM coaches
        WHERE user_id = %s
        """,
        (coach_id,),
    )
    row = cur.fetchone()

    # Eğer coach kaydı yoksa 404 (istersen otomatik create de yaparız)
    if not row:
        raise HTTPException(status_code=404, detail="Coach profile not found")

    return {"profile": row}


@router.put("/me/profile")
def update_my_profile(
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Sadece izin verdiğimiz alanları alalım (güvenlik + kontrol)
    allowed_fields = {
        "bio",
        "photo_url",
        "price_per_month",
        "specialties",
        "instagram",
        "is_active",
    }

    updates = {k: payload.get(k) for k in payload.keys() if k in allowed_fields}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    # Dynamic SET oluştur
    set_parts = []
    values = []
    i = 1
    for k, v in updates.items():
        set_parts.append(f"{k} = %s")
        values.append(v)
        i += 1

    values.append(coach_id)

    cur.execute(
        f"""
        UPDATE coaches
        SET {", ".join(set_parts)}
        WHERE user_id = %s
        RETURNING
            user_id,
            bio,
            photo_url,
            price_per_month,
            rating,
            rating_count,
            specialties,
            instagram,
            is_active
        """,
        tuple(values),
    )

    row = cur.fetchone()
    if not row:
        # coach satırı yoksa
        raise HTTPException(status_code=404, detail="Coach profile not found")

    db.commit()
    return {"ok": True, "profile": row}
