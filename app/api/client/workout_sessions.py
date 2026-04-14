"""Workout session tracking — persist exercise completion per day."""
from fastapi import Depends
from pydantic import BaseModel
from typing import List
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from app.services.badges import check_and_award
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

    # Activity log + push notification
    try:
        cur.execute("SELECT assigned_coach_id FROM clients WHERE user_id = %s", (uid,))
        client = cur.fetchone()
        coach_id = client["assigned_coach_id"] if client else None

        cur.execute("SELECT full_name FROM users WHERE id = %s", (uid,))
        u = cur.fetchone()
        name = u["full_name"] if u else "Öğrenci"

        day_labels = {"mon": "Pazartesi", "tue": "Salı", "wed": "Çarşamba", "thu": "Perşembe", "fri": "Cuma", "sat": "Cumartesi", "sun": "Pazar"}
        day_label = day_labels.get(body.day_key, body.day_key)

        from app.services.activity_log import log_activity
        log_activity(
            client_user_id=uid,
            coach_user_id=coach_id,
            action_type="workout_complete",
            title=f"{name} {day_label} antrenmanını tamamladı",
        )

        if coach_id:
            from app.services.push_notification import send_notification
            send_notification(
                coach_id,
                "Antrenman Tamamlandı",
                f"{name} {day_label} antrenmanını tamamladı.",
                {"type": "workout_complete", "client_user_id": str(uid)},
            )
    except Exception:
        pass

    # Award workout badge (fail-safe)
    newly_earned = []
    try:
        newly_earned = check_and_award(uid, 'workout_completed', db)
    except Exception:
        pass

    return {
        "completed_ids": row["completed_ids"] if row else [],
        "is_finished": row["is_finished"] if row else True,
        "newly_earned": newly_earned,
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


@router.get("/workout-sessions/week")
def get_week_sessions(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Get this week's finished days (mon-sun). Returns which days are completed."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT day_key, is_finished
           FROM workout_sessions
           WHERE user_id = %s
             AND session_date >= date_trunc('week', CURRENT_DATE)
             AND session_date < date_trunc('week', CURRENT_DATE) + interval '7 days'""",
        (current_user["id"],),
    )
    rows = cur.fetchall()
    finished_days = {r["day_key"]: r["is_finished"] for r in rows}
    return {"finished_days": finished_days}
