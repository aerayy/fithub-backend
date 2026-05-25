"""Stage 7 (persistence) — write a WeeklyProgram to workout_programs +
workout_days + workout_exercises.

Mirrors the v2 endpoint's persistence pattern so the Flutter app reads
v3 programs through the exact same SELECT queries. The only differences:
  * pipeline_version='v3' tag
  * validation_score column populated
  * training_profile_id link
  * exercise_library_id always resolved (we already have the id, no
    canonical_name matching needed)
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from psycopg2.extras import RealDictCursor

from .models import WeeklyProgram

logger = logging.getLogger(__name__)

# day_index → workout_days.day_of_week token (v2 convention)
_DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def save_program(
    conn,
    program: WeeklyProgram,
    *,
    coach_user_id: int,
    title: Optional[str] = None,
    validation_score: Optional[int] = None,
    training_profile_id: Optional[int] = None,
    is_active: bool = False,
) -> int:
    """Persist a WeeklyProgram. Returns workout_programs.id.

    Args:
        coach_user_id: who is the assigned coach? (AI coach = 60)
        title: human label; defaults to "AI Programi — {split_id}"
        is_active: False = draft (coach review). True = live.
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    user_id = program.profile.user_id
    title = title or f"AI Programi — {program.split.split_id}"

    # Header — pipeline_version + validation_score columns from migration 048
    cur.execute(
        """
        INSERT INTO workout_programs (
            client_user_id, coach_user_id, title, is_active,
            pipeline_version, validation_score, training_profile_id
        )
        VALUES (%s, %s, %s, %s, 'v3', %s, %s)
        RETURNING id
        """,
        (user_id, coach_user_id, title, is_active, validation_score, training_profile_id),
    )
    program_id: int = cur.fetchone()["id"]

    # 7 days, marking rest days explicitly. Iterate Mon..Sun.
    sessions_by_day = {s.day_index: s for s in program.sessions}
    target_by_day = {t.day_index: t for t in program.targets.sessions}

    # Pre-resolve canonical names in one query (cheap, avoids N+1)
    all_ex_ids = list({e.exercise_id for s in program.sessions for e in s.exercises})
    name_by_id: dict[int, str] = {}
    if all_ex_ids:
        cur.execute(
            "SELECT id, canonical_name FROM exercise_library WHERE id = ANY(%s)",
            (all_ex_ids,),
        )
        name_by_id = {r["id"]: r["canonical_name"] for r in cur.fetchall()}

    for day_idx in range(7):
        day_key = _DAY_KEYS[day_idx]
        session = sessions_by_day.get(day_idx)

        # Build day_payload in v2-compatible shape so the existing Flutter
        # antrenman view (which expects blocks[].items[]) renders v3
        # programs unchanged. Rest days keep blocks=[] like v2 did.
        if session is None:
            day_payload = {
                "kcal": "",
                "blocks": [],
                "warmup": {"items": [], "duration_min": ""},
                "coach_note": "Dinlenme",
            }
        else:
            items = []
            for ex in session.exercises:
                items.append({
                    "name": name_by_id.get(ex.exercise_id, f"#{ex.exercise_id}"),
                    "reps": ex.reps,
                    "sets": ex.sets,
                    "type": "exercise",
                    "notes": f"RIR {ex.rir}. {ex.rationale}".strip(". ").strip(),
                    "exercise_library_id": ex.exercise_id,
                    "rir": ex.rir,
                })
            day_payload = {
                "kcal": "",
                "blocks": [
                    {
                        "title": session.session_name,
                        "items": items,
                    }
                ],
                "warmup": {"items": [], "duration_min": ""},
                "coach_note": session.session_name,
            }

        cur.execute(
            """
            INSERT INTO workout_days (workout_program_id, day_of_week, order_index, day_payload)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (program_id, day_key, day_idx, json.dumps(day_payload)),
        )
        workout_day_id: int = cur.fetchone()["id"]

        if not session:
            continue

        # workout_exercises side-channel: some screens query this table
        # directly (gif_url join, set tracking). Keep it populated in
        # parallel with day_payload.
        for ex_order, ex in enumerate(session.exercises, start=1):
            canonical_name = name_by_id.get(ex.exercise_id, f"#{ex.exercise_id}")
            cur.execute(
                """
                INSERT INTO workout_exercises (
                    workout_day_id, exercise_name, sets, reps, notes,
                    order_index, exercise_library_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    workout_day_id,
                    canonical_name,
                    ex.sets,
                    ex.reps,
                    f"RIR {ex.rir}. {ex.rationale}".strip(". ").strip(),
                    ex_order,
                    ex.exercise_id,
                ),
            )

    conn.commit()
    logger.info(
        "persistence: saved v3 program_id=%s user_id=%s coach=%s score=%s",
        program_id, user_id, coach_user_id, validation_score,
    )
    return program_id
