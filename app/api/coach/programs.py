from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
import json
import re
from app.core.database import get_db
from app.core.security import require_role

router = APIRouter()

def normalize_name(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "", s)   # boşluk, tire, parantez vs hepsi gider
    return s

def resolve_exercise_library_id(cur, name: str):
    if not name:
        return None

    raw = name.strip()
    n = normalize_name(raw)
    if not n:
        return None

    # 1) Önce direkt ILIKE ile hızlı dene (bazen tutar)
    cur.execute(
        """
        SELECT id
        FROM exercise_library
        WHERE canonical_name ILIKE %s
           OR external_id ILIKE %s
           OR (aliases IS NOT NULL AND EXISTS (
                SELECT 1 FROM unnest(aliases) a WHERE a ILIKE %s
           ))
        ORDER BY
          CASE WHEN canonical_name ILIKE %s THEN 0 ELSE 1 END,
          canonical_name ASC
        LIMIT 1
        """,
        (f"%{raw}%", f"%{raw}%", f"%{raw}%", raw),
    )
    row = cur.fetchone()
    if row:
        return row["id"] if isinstance(row, dict) else row[0]

    # 2) Asıl çözüm: DB tarafında normalize edip compare et
    cur.execute(
        """
        WITH q AS (SELECT %s::text AS qnorm)
        SELECT id
        FROM exercise_library, q
        WHERE regexp_replace(lower(canonical_name), '[^a-z0-9]+', '', 'g')
              LIKE ('%' || q.qnorm || '%')
           OR regexp_replace(lower(external_id), '[^a-z0-9]+', '', 'g')
              LIKE ('%' || q.qnorm || '%')
           OR (aliases IS NOT NULL AND EXISTS (
                SELECT 1
                FROM unnest(aliases) a
                WHERE regexp_replace(lower(a), '[^a-z0-9]+', '', 'g')
                      LIKE ('%' || q.qnorm || '%')
           ))
        ORDER BY length(canonical_name) ASC
        LIMIT 1
        """,
        (n,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return row["id"] if isinstance(row, dict) else row[0]





def _fetchone_id(row):
    if row is None:
        return None
    if isinstance(row, dict):
        if "id" in row:
            return row["id"]
        return next(iter(row.values()))
    return row[0]


@router.get("/students/{student_user_id}/active-programs")
def get_active_programs(
    student_user_id: int,
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
                e.created_at, e.updated_at, el.gif_url
            FROM workout_exercises e
            JOIN workout_days d ON d.id = e.workout_day_id
            LEFT JOIN exercise_library el ON el.id = e.exercise_library_id
            WHERE d.workout_program_id=%s
            ORDER BY d.order_index ASC, e.order_index ASC, e.id ASC
            """,
            (program_id,),
        )
        workout_exercises = cur.fetchall()

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
            exercise_name = (ex.get("name") or "").strip()
            exercise_library_id = ex.get("exercise_library_id")  # UI bunu gönderecek

            if not exercise_library_id:
                exercise_library_id = resolve_exercise_library_id(cur, exercise_name)

            cur.execute(
                """
                INSERT INTO workout_exercises
                (workout_day_id, exercise_name, exercise_library_id, sets, reps, notes, order_index)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    workout_day_id,
                    exercise_name,
                    exercise_library_id,
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
    day_meals = week.get("mon") or next(
        (week[k] for k in ["tue", "wed", "thu", "fri", "sat", "sun"] if week.get(k)),
        [],
    )
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
