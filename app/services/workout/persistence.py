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
    microcycle: Optional[list] = None,
) -> int:
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

    # Pre-resolve canonical names ONCE (across all 4 weeks if microcycle).
    all_programs = [program]
    if microcycle:
        all_programs = [p for _, _, p in microcycle]
    all_ex_ids = list({
        e.exercise_id
        for p in all_programs
        for s in p.sessions
        for e in s.exercises
    })
    name_by_id: dict[int, str] = {}
    if all_ex_ids:
        cur.execute(
            "SELECT id, canonical_name FROM exercise_library WHERE id = ANY(%s)",
            (all_ex_ids,),
        )
        name_by_id = {r["id"]: r["canonical_name"] for r in cur.fetchall()}

    def _write_week(week_index: int, week_program: WeeklyProgram) -> None:
        """Inner helper — writes 7 workout_days + their workout_exercises
        for one week."""
        _write_week_rows(
            cur=cur,
            program_id=program_id,
            week_index=week_index,
            week_program=week_program,
            name_by_id=name_by_id,
        )

    if microcycle:
        for week_index, strategy, week_program in microcycle:
            _write_week(week_index, week_program)
            # program_microcycles audit row
            cur.execute(
                """
                INSERT INTO program_microcycles
                  (workout_program_id, week_number, delta_strategy, delta_payload, notes)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (workout_program_id, week_number) DO NOTHING
                """,
                (program_id, week_index, strategy, json.dumps({}), None),
            )
    else:
        _write_week(1, program)

    conn.commit()
    logger.info(
        "persistence: saved v3 program_id=%s user_id=%s coach=%s score=%s weeks=%s",
        program_id, user_id, coach_user_id, validation_score,
        len(microcycle) if microcycle else 1,
    )
    return program_id


def _default_warmup(session_name: str) -> dict:
    """Oturum tipine göre standart ısınma (v3 pipeline ısınma üretmiyor; boş
    bırakılınca uygulamada süresiz/boş "Isınma Akışı" kartı görünüyordu).
    Flutter kartı {"duration_min": str, "items": [{"name","description"}]} bekler.
    """
    n = (session_name or "").lower()
    base = [
        {"name": "Hafif kardiyo", "description": "3-5 dk yürüyüş, bisiklet veya ip atlama — nabzı hafifçe yükselt."},
    ]
    upper_keys = ("upper", "üst", "push", "pull", "chest", "back", "shoulder", "arm", "göğüs", "sırt", "omuz", "kol")
    lower_keys = ("lower", "leg", "alt", "bacak", "glute", "kalça")
    if any(k in n for k in upper_keys):
        specific = [
            {"name": "Omuz çevirme + kol daireleri", "description": "Her yöne 10-15 tekrar, kontrollü."},
            {"name": "Band pull-apart / scapular push-up", "description": "2×15 — omuz kuşağını uyandır."},
        ]
    elif any(k in n for k in lower_keys):
        specific = [
            {"name": "Kalça açıcı + bacak salınımı", "description": "Her bacak 10-12 tekrar, ileri-geri ve yana."},
            {"name": "Vücut ağırlığı squat", "description": "2×12 — tam hareket açıklığı, yavaş iniş."},
        ]
    else:
        specific = [
            {"name": "Dinamik esneme", "description": "Kol daireleri, kalça açıcı, gövde rotasyonu — toplam 3-4 dk."},
            {"name": "Vücut ağırlığı squat + şınav", "description": "2×10 — tüm vücudu uyandır."},
        ]
    ramp = {"name": "İlk hareketin hafif setleri", "description": "Çalışma ağırlığının %40-60'ı ile 1-2 set, 8-10 tekrar."}
    return {"duration_min": "8", "items": base + specific + [ramp]}


def _write_week_rows(*, cur, program_id, week_index, week_program, name_by_id) -> None:
    """Write 7 workout_days rows + their workout_exercises for one week_index."""
    sessions_by_day = {s.day_index: s for s in week_program.sessions}
    target_by_day = {t.day_index: t for t in week_program.targets.sessions}

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
                "warmup": _default_warmup(session.session_name),
                "coach_note": session.session_name,
            }

        cur.execute(
            """
            INSERT INTO workout_days (workout_program_id, week_index, day_of_week, order_index, day_payload)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (program_id, week_index, day_key, day_idx, json.dumps(day_payload)),
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
