# app/api/admin.py
from fastapi import APIRouter, Depends, HTTPException
import bcrypt
from psycopg2.extras import RealDictCursor
import psycopg2

from app.core.security import require_role, verify_admin_key
from app.core.database import get_db
from app.schemas.admin import CreateCoachRequest

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
          u.profile_photo_url,
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
        """
        SELECT *
        FROM client_onboarding
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 1
        """,
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

        # ✅ workout_days schema:
        # id, workout_program_id, day_of_week, order_index
        cur.execute(
            """
            SELECT
              id,
              day_of_week,
              order_index
            FROM workout_days
            WHERE workout_program_id = %s
            ORDER BY order_index ASC, id ASC
            """,
            (wp_id,),
        )
        workout_days = cur.fetchall() or []

        # ✅ workout_exercises schema:
        # id, workout_day_id, exercise_name, sets, reps, notes, order_index
        # Burada program_id yok, bu yüzden days üzerinden filtreliyoruz.
        cur.execute(
            """
            SELECT
              we.id,
              we.workout_day_id,
              we.exercise_name,
              we.sets,
              we.reps,
              we.notes,
              we.order_index
            FROM workout_exercises we
            JOIN workout_days wd ON wd.id = we.workout_day_id
            WHERE wd.workout_program_id = %s
            ORDER BY we.workout_day_id ASC, we.order_index ASC, we.id ASC
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

        # ✅ nutrition_meals schema:
        # id, nutrition_program_id, meal_type, content, order_index
        cur.execute(
            """
            SELECT id, meal_type, content, order_index
            FROM nutrition_meals
            WHERE nutrition_program_id = %s
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


@router.post("/coaches")
def create_coach(
    req: CreateCoachRequest,
    db=Depends(get_db),
    _admin_key=Depends(verify_admin_key),
):
    """
    Create a new coach account.
    
    This endpoint creates both:
    1. A user record with role="coach"
    2. A coach record with coach-specific details
    
    Requires X-Admin-Key header matching ADMIN_API_KEY environment variable.
    """
    cur = db.cursor(cursor_factory=RealDictCursor)
    
    # Store original autocommit setting
    original_autocommit = db.autocommit
    
    try:
        # Start transaction (psycopg2 autocommit is False by default, but be explicit)
        db.autocommit = False
        
        # Hash password using the same method as /auth/signup
        hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
        
        # Insert into users table with role="coach"
        cur.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            RETURNING id, email, full_name, role, created_at, updated_at
            """,
            (req.email, hashed, req.full_name, "coach"),
        )
        user = cur.fetchone()
        user_id = user["id"]
        
        # Prepare specialties array (PostgreSQL text[]) - use empty array if None
        specialties_array = req.specialties if req.specialties else []
        
        # Insert into coaches table
        cur.execute(
            """
            INSERT INTO coaches (
                user_id, bio, photo_url, price_per_month, 
                rating, rating_count, specialties, instagram, is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING user_id, bio, photo_url, price_per_month, 
                     rating, rating_count, specialties, instagram, is_active
            """,
            (
                user_id,
                req.bio,
                req.photo_url,
                req.price_per_month,
                req.rating,
                req.rating_count if req.rating_count is not None else 0,
                specialties_array,  # psycopg2 will handle array conversion
                req.instagram,
                req.is_active if req.is_active is not None else True,
            ),
        )
        coach = cur.fetchone()
        
        # Commit transaction
        db.commit()
        
        return {
            "user_id": user_id,
            "user": dict(user),
            "coach": dict(coach),
        }
        
    except psycopg2.IntegrityError as e:
        # Rollback on database constraint violations
        db.rollback()
        # Check if it's a unique violation (email already exists)
        if e.pgcode == "23505":  # UniqueViolation error code
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )
        # Other integrity errors
        raise HTTPException(
            status_code=400,
            detail=f"Database constraint violation: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions after rollback
        db.rollback()
        raise
    except Exception as e:
        # Rollback on any other error
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create coach: {str(e)}"
        )
    finally:
        # Restore original autocommit setting
        db.autocommit = original_autocommit
