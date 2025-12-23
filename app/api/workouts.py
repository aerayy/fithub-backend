from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from pydantic import BaseModel
from typing import List, Optional

from app.core.security import require_role

router = APIRouter(prefix="/workouts", tags=["workouts"])


# ---- Schemas ----
class ExerciseIn(BaseModel):
    exercise_name: str
    sets: Optional[int] = None
    reps: Optional[str] = None  # '8-10' gibi
    notes: Optional[str] = None
    order_index: int = 0


class DayIn(BaseModel):
    day_of_week: str  # 'mon','tue'...
    order_index: int = 0
    exercises: List[ExerciseIn] = []


class WorkoutProgramCreate(BaseModel):
    client_user_id: int
    coach_user_id: int
    title: str = "Workout Program"
    week_number: int = 1
    days: List[DayIn] = []


# ---- Helpers ----
def fetch_active_program(client_user_id: int, db):
    cur = db.cursor()

    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, title, week_number, is_active, created_at, updated_at
        FROM workout_programs
        WHERE client_user_id = %s AND is_active = TRUE
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (client_user_id,),
    )
    program = cur.fetchone()
    if not program:
        return None

    program_id = program["id"]

    cur.execute(
        """
        SELECT id, day_of_week, order_index
        FROM workout_days
        WHERE workout_program_id = %s
        ORDER BY order_index ASC, id ASC
        """,
        (program_id,),
    )
    days = cur.fetchall() or []

    for d in days:
        cur.execute(
            """
            SELECT id, exercise_name, sets, reps, notes, order_index
            FROM workout_exercises
            WHERE workout_day_id = %s
            ORDER BY order_index ASC, id ASC
            """,
            (d["id"],),
        )
        d["exercises"] = cur.fetchall() or []

    program["days"] = days
    return program


# ---- Endpoints ----
@router.get("/active/{client_user_id}")
def get_active_workout(
    client_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("client", "coach")),
):
    # client sadece kendi programını görebilsin
    if current_user["role"] == "client" and current_user["id"] != client_user_id:
        raise HTTPException(status_code=403, detail="You can only access your own program")

    program = fetch_active_program(client_user_id, db)
    if not program:
        raise HTTPException(status_code=404, detail="Active workout program not found")

    return {"program": program}


@router.post("/set-active")
def set_active_workout(
    payload: WorkoutProgramCreate,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Koç program kaydeder:
    1) Mevcut aktif programı pasif yap
    2) Yeni programı aktif oluştur
    3) Günleri + egzersizleri ekle
    """

    # Token'daki koç id'si ile payload'daki aynı olmalı
    if current_user["id"] != payload.coach_user_id:
        raise HTTPException(status_code=403, detail="coach_user_id mismatch")

    cur = db.cursor()

    try:
        # 1) mevcut aktifi pasifle
        cur.execute(
            """
            UPDATE workout_programs
            SET is_active = FALSE, updated_at = NOW()
            WHERE client_user_id = %s AND is_active = TRUE
            """,
            (payload.client_user_id,),
        )

        # 2) yeni programı ekle
        cur.execute(
            """
            INSERT INTO workout_programs (client_user_id, coach_user_id, title, week_number, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, TRUE, NOW(), NOW())
            RETURNING id, client_user_id, coach_user_id, title, week_number, is_active, created_at, updated_at
            """,
            (
                payload.client_user_id,
                payload.coach_user_id,
                payload.title,
                payload.week_number,
            ),
        )
        program = cur.fetchone()
        program_id = program["id"]

        # 3) günleri ve egzersizleri ekle
        for day in payload.days:
            cur.execute(
                """
                INSERT INTO workout_days (workout_program_id, day_of_week, order_index, created_at, updated_at)
                VALUES (%s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (program_id, day.day_of_week, day.order_index),
            )
            day_id = cur.fetchone()["id"]

            for ex in day.exercises:
                cur.execute(
                    """
                    INSERT INTO workout_exercises (workout_day_id, exercise_name, sets, reps, notes, order_index, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (day_id, ex.exercise_name, ex.sets, ex.reps, ex.notes, ex.order_index),
                )

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # yeni aktifi geri döndür
    program = fetch_active_program(payload.client_user_id, db)
    return {"program": program}
