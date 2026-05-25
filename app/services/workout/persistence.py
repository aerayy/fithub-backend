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

    for day_idx in range(7):
        day_key = _DAY_KEYS[day_idx]
        session = sessions_by_day.get(day_idx)
        if session is None:
            day_payload = {
                "is_rest": True,
                "session_title": "Dinlenme",
                "exercises": [],
            }
        else:
            day_payload = {
                "is_rest": False,
                "session_title": session.session_name,
                "exercises_count": len(session.exercises),
                "set_target": target_by_day.get(day_idx).total_set_budget if target_by_day.get(day_idx) else None,
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

        for ex_order, ex in enumerate(session.exercises, start=1):
            # Look up canonical name once — we already have exercise_library_id
            cur.execute(
                "SELECT canonical_name FROM exercise_library WHERE id = %s",
                (ex.exercise_id,),
            )
            row = cur.fetchone()
            canonical_name = row["canonical_name"] if row else f"#{ex.exercise_id}"

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
                    # RIR + rationale → notes payload for now (mobile parses as text)
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
