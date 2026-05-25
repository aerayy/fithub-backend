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
    Returns: program dict with days list, each day has day_payload, week_index
    and exercises. v3 microcycle programs return 28 day rows (4 weeks × 7).
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

    # Fetch days with day_payload + week_index (migration 051)
    cur.execute(
        """
        SELECT id, workout_program_id, week_index, day_of_week, order_index, day_payload, created_at, updated_at
        FROM workout_days
        WHERE workout_program_id = %s
        ORDER BY week_index ASC, order_index ASC, id ASC
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
                   we.notes, we.order_index, we.exercise_library_id, el.gif_url
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
        if ex.get("exercise_library_id"):
            item["library_id"] = ex["exercise_library_id"]
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
    Inject gif_url and library_id from exercise records into day_payload items by matching exercise name.
    """
    # Build name -> {gif_url, library_id} lookup from exercises
    lookup = {}
    for ex in exercises:
        name = (ex.get("exercise_name") or "").strip().lower()
        if name:
            lookup[name] = {
                "gif_url": ex.get("gif_url"),
                "library_id": ex.get("exercise_library_id"),
            }

    if not lookup:
        return payload

    for block in payload.get("blocks", []):
        for item in block.get("items", []):
            name = (item.get("name") or "").strip().lower()
            if name and name in lookup:
                data = lookup[name]
                if data["gif_url"] and "gif_url" not in item:
                    item["gif_url"] = data["gif_url"]
                if data["library_id"] and "library_id" not in item:
                    item["library_id"] = data["library_id"]

    return payload


def _fetch_universal_fallback_gif(cur) -> Optional[str]:
    """KIRMIZI CIZGI safety net: gif'i olan evrensel bir hareket (Plank) URL'i.
    Read endpoint'inde herhangi bir egzersizin gif_url'i bos kalirsa bununla doldurulur.
    Boylece UI hicbir zaman 'GORSEL EKLENMEDI' gostermez."""
    cur.execute(
        """SELECT gif_url FROM exercise_library
           WHERE canonical_name ILIKE 'Plank'
             AND gif_url IS NOT NULL AND gif_url != ''
           LIMIT 1"""
    )
    row = cur.fetchone()
    if row:
        # row dict (RealDictCursor) veya tuple olabilir
        return row.get("gif_url") if hasattr(row, "get") else row[0]
    # Plank yoksa gif'i olan herhangi bir hareket
    cur.execute(
        "SELECT gif_url FROM exercise_library WHERE gif_url IS NOT NULL AND gif_url != '' LIMIT 1"
    )
    row = cur.fetchone()
    if row:
        return row.get("gif_url") if hasattr(row, "get") else row[0]
    return None


def _ensure_all_items_have_gif(payload: Dict, fallback_gif_url: Optional[str]) -> None:
    """Inject sonrasi son guvenlik agi: bos kalan her item'a fallback URL'i koy."""
    if not fallback_gif_url:
        return
    for block in payload.get("blocks", []):
        for item in block.get("items", []):
            current = item.get("gif_url")
            if not current or not str(current).strip():
                item["gif_url"] = fallback_gif_url


def build_week_response(program: Dict, days: List[Dict], fallback_gif_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Build the week response structure from program and days.
    Returns: { "mon": dayPayloadOrNull, "tue": ..., ... }

    fallback_gif_url: KIRMIZI CIZGI safety net — bos gif_url'lere bu URL atanir.
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
                    # Defansif son katman: hala bos kalan item varsa fallback URL koy
                    _ensure_all_items_have_gif(payload, fallback_gif_url)
                    week[day_key] = payload
                    continue
            except (json.JSONDecodeError, TypeError):
                pass  # Fall through to backward compatibility

        # Backward compatibility: build from exercises
        if exercises:
            payload = build_day_payload_from_flat_exercises(exercises, program_title)
            _ensure_all_items_have_gif(payload, fallback_gif_url)
            week[day_key] = payload
        # If no exercises and no payload, leave as None

    return week


@router.get("/workouts/active")
def get_active_workout_for_client(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Get active workout program for the authenticated client in UI-friendly format.

    v3 microcycle support: response includes `weeks` map (1..4) plus a
    flat `week` field pointing to the user's current microcycle week
    (computed from days since program creation). Old clients reading
    only `week` keep working.

    Returns:
    {
        "program": { id, title, week_number, created_at, updated_at, current_week_index },
        "week":  { "mon": ..., "tue": ..., ... }   // backward compat (current week)
        "weeks": { "1": {...}, "2": {...}, "3": {...}, "4": {...} }
    }
    """
    from datetime import datetime, timezone
    client_user_id = current_user["id"]

    try:
        program_data = fetch_active_program_with_payload(client_user_id, db)
        if not program_data:
            raise HTTPException(status_code=404, detail="Active workout program not found")

        cur = db.cursor(cursor_factory=RealDictCursor)
        fallback_gif = _fetch_universal_fallback_gif(cur)

        # Group days by week_index (v3 mikrosüvel için; v2 ve eski v3 = hepsi week 1)
        days_by_week: dict[int, list] = {}
        for d in program_data.get("days", []) or []:
            wk = d.get("week_index") or 1
            days_by_week.setdefault(wk, []).append(d)

        weeks_response: dict[str, dict] = {}
        for wk, day_rows in days_by_week.items():
            weeks_response[str(wk)] = build_week_response(program_data, day_rows, fallback_gif)

        # Compute "current week" from days since program creation
        created_at = program_data.get("created_at")
        current_week_index = 1
        if created_at:
            now = datetime.now(timezone.utc)
            created_aware = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
            days_since = (now - created_aware).days
            current_week_index = min(4, max(1, (days_since // 7) + 1))

        # Backward compat: top-level `week` = current week's data
        backward_week = weeks_response.get(str(current_week_index)) or weeks_response.get("1") or {}

        return {
            "program": {
                "id": program_data["id"],
                "title": program_data.get("title") or "",
                "week_number": program_data.get("week_number") or 1,
                "created_at": program_data.get("created_at"),
                "updated_at": program_data.get("updated_at"),
                "current_week_index": current_week_index,
                "total_weeks": len(weeks_response),
            },
            "week": backward_week,
            "weeks": weeks_response,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


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
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")
