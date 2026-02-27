from fastapi import Depends, HTTPException
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List
import json

from app.core.database import get_db
from app.core.security import require_role
from .routes import router


def fetch_active_program_with_payload(client_user_id: int, db):
    """
    Fetch active workout program with days (including day_payload) and exercises.
    Returns: program dict with days list, each day has day_payload and exercises.
    """
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Fetch active program
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

    # Fetch days with day_payload
    cur.execute(
        """
        SELECT id, workout_program_id, day_of_week, order_index, day_payload, created_at, updated_at
        FROM workout_days
        WHERE workout_program_id = %s
        ORDER BY order_index ASC, id ASC
        """,
        (program_id,),
    )
    days = cur.fetchall() or []

    # Fetch all exercises for all days
    day_ids = [d["id"] for d in days]
    exercises_by_day = {}
    if day_ids:
        placeholders = ",".join(["%s"] * len(day_ids))
        cur.execute(
            f"""
            SELECT we.id, we.workout_day_id, we.exercise_name, we.sets, we.reps,
                   we.notes, we.order_index, el.gif_url
            FROM workout_exercises we
            LEFT JOIN exercise_library el ON el.id = we.exercise_library_id
            WHERE we.workout_day_id IN ({placeholders})
            ORDER BY we.workout_day_id ASC, we.order_index ASC, we.id ASC
            """,
            tuple(day_ids),
        )
        all_exercises = cur.fetchall() or []
        for ex in all_exercises:
            day_id = ex["workout_day_id"]
            if day_id not in exercises_by_day:
                exercises_by_day[day_id] = []
            exercises_by_day[day_id].append(ex)

    # Attach exercises to days
    for d in days:
        d["exercises"] = exercises_by_day.get(d["id"], [])

    program["days"] = days
    return program


def build_day_payload_from_flat_exercises(exercises: List[Dict], program_title: str = "") -> Dict[str, Any]:
    """
    Build a day payload structure from flat exercise list (backward compatibility).
    Returns a day payload dict with title, coach_note, warmup, and blocks.
    """
    exercise_items = []
    for ex in exercises:
        item = {
            "type": "exercise",
            "name": ex.get("exercise_name") or "",
            "sets": ex.get("sets"),
            "reps": ex.get("reps") or "",
            "notes": ex.get("notes") or "",
        }
        if ex.get("gif_url"):
            item["gif_url"] = ex["gif_url"]
        exercise_items.append(item)

    return {
        "title": program_title or "",
        "kcal": "",
        "coach_note": "",
        "warmup": {
            "duration_min": "",
            "items": []
        },
        "blocks": [
            {
                "title": "Workout Block",
                "items": exercise_items
            }
        ]
    }


def _inject_gif_urls(payload: Dict, exercises: List[Dict]) -> Dict:
    """
    Inject gif_url from exercise records into day_payload items by matching exercise name.
    """
    # Build name -> gif_url lookup from exercises
    gif_lookup = {}
    for ex in exercises:
        name = (ex.get("exercise_name") or "").strip().lower()
        gif = ex.get("gif_url")
        if name and gif:
            gif_lookup[name] = gif

    if not gif_lookup:
        return payload

    for block in payload.get("blocks", []):
        for item in block.get("items", []):
            name = (item.get("name") or "").strip().lower()
            if name and name in gif_lookup and "gif_url" not in item:
                item["gif_url"] = gif_lookup[name]

    return payload


def build_week_response(program: Dict, days: List[Dict]) -> Dict[str, Any]:
    """
    Build the week response structure from program and days.
    Returns: { "mon": dayPayloadOrNull, "tue": ..., ... }
    """
    week_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    week = {day: None for day in week_days}

    program_title = program.get("title") or ""

    for day in days:
        day_key = day.get("day_of_week")
        if day_key not in week_days:
            continue

        day_payload = day.get("day_payload")
        exercises = day.get("exercises", [])

        # If day_payload exists and is valid JSON, use it
        if day_payload:
            try:
                if isinstance(day_payload, str):
                    payload = json.loads(day_payload)
                else:
                    payload = day_payload
                # Ensure it's a dict
                if isinstance(payload, dict):
                    # Inject gif_url from exercises into payload items
                    _inject_gif_urls(payload, exercises)
                    week[day_key] = payload
                    continue
            except (json.JSONDecodeError, TypeError):
                pass  # Fall through to backward compatibility

        # Backward compatibility: build from exercises
        if exercises:
            week[day_key] = build_day_payload_from_flat_exercises(exercises, program_title)
        # If no exercises and no payload, leave as None

    return week


@router.get("/workouts/active")
def get_active_workout_for_client(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Get active workout program for the authenticated client in UI-friendly format.
    Returns:
    {
        "program": { id, title, week_number, created_at, updated_at },
        "week": {
            "mon": dayPayloadOrNull,
            "tue": ...,
            ...
        }
    }
    """
    client_user_id = current_user["id"]

    try:
        program_data = fetch_active_program_with_payload(client_user_id, db)
        if not program_data:
            raise HTTPException(status_code=404, detail="Active workout program not found")

        # Build week response
        week = build_week_response(program_data, program_data.get("days", []))

        # Return in the requested format
        return {
            "program": {
                "id": program_data["id"],
                "title": program_data.get("title") or "",
                "week_number": program_data.get("week_number") or 1,
                "created_at": program_data.get("created_at"),
                "updated_at": program_data.get("updated_at"),
            },
            "week": week
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/cardio/active")
def get_active_cardio_for_client(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Get active cardio program for the authenticated client.
    Returns:
    {
        "program": { "id", "title", "created_at" } or null,
        "sessions": [...]
    }
    """
    client_user_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        # Fetch active cardio program
        cur.execute(
            """
            SELECT id, title, created_at
            FROM cardio_programs
            WHERE client_user_id=%s AND is_active=TRUE
            ORDER BY id DESC
            LIMIT 1
            """,
            (client_user_id,),
        )
        program = cur.fetchone()

        if not program:
            return {"program": None, "sessions": []}

        program_id = program["id"]

        # Fetch sessions for this program
        cur.execute(
            """
            SELECT id, cardio_program_id, day_of_week, cardio_type, duration_min, notes, order_index, created_at
            FROM cardio_sessions
            WHERE cardio_program_id=%s
            ORDER BY order_index ASC, id ASC
            """,
            (program_id,),
        )
        sessions = cur.fetchall() or []

        return {
            "program": {
                "id": program["id"],
                "title": program.get("title") or "",
                "created_at": program.get("created_at"),
            },
            "sessions": sessions,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
