"""Workout session tracking — persist exercise completion per day."""
from fastapi import Depends
from pydantic import BaseModel
from typing import List
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


class ToggleExerciseInput(BaseModel):
    day_key: str  # 'mon','tue', etc.
    exercise_id: str


class FinishWorkoutInput(BaseModel):
    day_key: str


@router.post("/workout-sessions/toggle")
def toggle_exercise(
    body: ToggleExerciseInput,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Toggle an exercise done/undone for today. Returns updated list."""
    uid = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Upsert session row
    cur.execute(
        """INSERT INTO workout_sessions (user_id, session_date, day_key, completed_ids)
           VALUES (%s, CURRENT_DATE, %s, ARRAY[%s]::text[])
           ON CONFLICT (user_id, session_date, day_key)
           DO UPDATE SET
             completed_ids = CASE
               WHEN %s = ANY(workout_sessions.completed_ids)
               THEN array_remove(workout_sessions.completed_ids, %s)
               ELSE array_append(workout_sessions.completed_ids, %s)
             END,
             updated_at = NOW()
           RETURNING completed_ids, is_finished""",
        (uid, body.day_key, body.exercise_id,
         body.exercise_id, body.exercise_id, body.exercise_id),
    )
    db.commit()
    row = cur.fetchone()
    return {
        "completed_ids": row["completed_ids"] if row else [],
        "is_finished": row["is_finished"] if row else False,
    }


@router.post("/workout-sessions/finish")
def finish_workout(
    body: FinishWorkoutInput,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Mark today's workout as finished."""
    uid = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """INSERT INTO workout_sessions (user_id, session_date, day_key, is_finished)
           VALUES (%s, CURRENT_DATE, %s, TRUE)
           ON CONFLICT (user_id, session_date, day_key)
           DO UPDATE SET is_finished = TRUE, updated_at = NOW()
           RETURNING completed_ids, is_finished""",
        (uid, body.day_key),
    )
    db.commit()
    row = cur.fetchone()
    return {
        "completed_ids": row["completed_ids"] if row else [],
        "is_finished": row["is_finished"] if row else True,
    }


@router.get("/workout-sessions/today")
def get_today_session(
    day_key: str = "mon",
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Get today's workout session state for a given day."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT completed_ids, is_finished
           FROM workout_sessions
           WHERE user_id = %s AND session_date = CURRENT_DATE AND day_key = %s""",
        (current_user["id"], day_key),
    )
    row = cur.fetchone()
    return {
        "completed_ids": row["completed_ids"] if row else [],
        "is_finished": row["is_finished"] if row else False,
    }
