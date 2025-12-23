# app/api/admin.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_role
from app.core.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

def _ensure_student_access(db, coach_user_id: int, student_user_id: int):
    cur = db.cursor()
    cur.execute(
        """
        SELECT user_id, assigned_coach_id
        FROM clients
        WHERE user_id = %s
        """,
        (student_user_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    # row dict değilse indexli olabilir:
    assigned = row["assigned_coach_id"] if isinstance(row, dict) else row[1]
    if assigned != coach_user_id:
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

@router.get("/students")
def list_students(
    db=Depends(get_db),
    user=Depends(require_role("coach", "superadmin")),
):
    user_id = user["id"] if isinstance(user, dict) else user[0]
    role = user["role"] if isinstance(user, dict) else user[2]

    cur = db.cursor()

    if role == "coach":
        cur.execute(
            """
            SELECT
              u.id AS user_id,
              u.full_name,
              u.email,
              u.timezone,
              u.updated_at,
              c.goal_type,
              c.activity_level,
              c.onboarding_done,
              c.assigned_coach_id
            FROM clients c
            JOIN users u ON u.id = c.user_id
            WHERE c.assigned_coach_id = %s
            ORDER BY u.updated_at DESC NULLS LAST, u.id DESC
            """,
            (user_id,),
        )
    else:
        # superadmin hepsini görsün
        cur.execute(
            """
            SELECT
              u.id AS user_id,
              u.full_name,
              u.email,
              u.timezone,
              u.updated_at,
              c.goal_type,
              c.activity_level,
              c.onboarding_done,
              c.assigned_coach_id
            FROM clients c
            JOIN users u ON u.id = c.user_id
            ORDER BY u.updated_at DESC NULLS LAST, u.id DESC
            """
        )

    rows = cur.fetchall() or []
    return {"items": rows}


@router.get("/students/{student_user_id}")
def get_student_detail(
    student_user_id: int,
    db=Depends(get_db),
    user=Depends(require_role("coach", "superadmin")),
):
    user_id = user["id"] if isinstance(user, dict) else user[0]
    role = user["role"] if isinstance(user, dict) else user[2]

    if role == "coach":
        _ensure_student_access(db, coach_user_id=user_id, student_user_id=student_user_id)

    cur = db.cursor()

    # 1) Basic user + client
    cur.execute(
        """
        SELECT
          u.id AS user_id,
          u.full_name,
          u.email,
          u.timezone,
          u.created_at,
          u.updated_at,
          c.gender,
          c.date_of_birth,
          c.height_cm,
          c.weight_kg,
          c.goal_type,
          c.activity_level,
          c.onboarding_done,
          c.assigned_coach_id
        FROM users u
        JOIN clients c ON c.user_id = u.id
        WHERE u.id = %s
        """,
        (student_user_id,),
    )
    student = cur.fetchone()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 2) Onboarding (varsa)
    cur.execute(
        "SELECT * FROM client_onboarding WHERE user_id = %s ORDER BY id DESC LIMIT 1",
        (student_user_id,),
    )
    onboarding = cur.fetchone()

    # 3) Active workout program (varsa)
    cur.execute(
        """
        SELECT id, title, week_number, is_active, created_at, updated_at
        FROM workout_programs
        WHERE client_user_id = %s AND is_active = TRUE
        ORDER BY updated_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
        (student_user_id,),
    )
    workout_program = cur.fetchone()

    workout_days = []
    workout_exercises = []
    if workout_program:
        wp_id = workout_program["id"] if isinstance(workout_program, dict) else workout_program[0]
        cur.execute(
            """
            SELECT id, day_name, order_index
            FROM workout_days
            WHERE program_id = %s
            ORDER BY order_index ASC, id ASC
            """,
            (wp_id,),
        )
        workout_days = cur.fetchall() or []

        cur.execute(
            """
            SELECT id, day_id, name, sets, reps, notes, order_index
            FROM workout_exercises
            WHERE program_id = %s
            ORDER BY day_id ASC, order_index ASC, id ASC
            """,
            (wp_id,),
        )
        workout_exercises = cur.fetchall() or []

    # 4) Active nutrition program (varsa)
    cur.execute(
        """
        SELECT id, title, is_active, created_at, updated_at
        FROM nutrition_programs
        WHERE client_user_id = %s AND is_active = TRUE
        ORDER BY updated_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
        (student_user_id,),
    )
    nutrition_program = cur.fetchone()

    meals = []
    if nutrition_program:
        np_id = nutrition_program["id"] if isinstance(nutrition_program, dict) else nutrition_program[0]
        cur.execute(
            """
            SELECT id, meal_type, content, order_index
            FROM nutrition_meals
            WHERE program_id = %s
            ORDER BY order_index ASC, id ASC
            """,
            (np_id,),
        )
        meals = cur.fetchall() or []

    return {
        "student": student,
        "onboarding": onboarding,
        "active_programs": {
            "workout_program": workout_program,
            "workout_days": workout_days,
            "workout_exercises": workout_exercises,
            "nutrition_program": nutrition_program,
            "meals": meals,
        },
    }
