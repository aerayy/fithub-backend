"""Koç tarafı antrenman programı yazıcı/okuyucu — tek veya çok haftalı (week_index 1..4).

Manuel kayıt (POST /coach/.../workout-programs), taslak atama ve zamanlanmış taslak
aktivasyonu AYNI yolu kullanır; böylece hepsi day_payload (yapısal gün) + workout_exercises
(düz liste, geriye uyumluluk) satırlarını tutarlı yazar.

Payload biçimleri (hepsi kabul edilir):
  {"weeks": {"1": week, "2": week, ...}}   çok haftalı (admin editör hafta sekmeleri)
  {"week": week}                           tek hafta (eski)
  week                                     doğrudan gün haritası (taslak payload'ı)
week = {"mon": day_payload | [exercise, ...] | None, ...}
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
MAX_WEEKS = 4


def normalize_weeks(payload: Any) -> Dict[int, dict]:
    """Payload'ı {week_index: week} haritasına çevirir (en az 1 hafta)."""
    if not isinstance(payload, dict):
        return {1: {}}
    if isinstance(payload.get("weeks"), dict) and payload["weeks"]:
        out: Dict[int, dict] = {}
        for k, v in payload["weeks"].items():
            try:
                idx = int(k)
            except (TypeError, ValueError):
                continue
            if 1 <= idx <= MAX_WEEKS and isinstance(v, dict):
                out[idx] = v
        if out:
            return out
    if isinstance(payload.get("week"), dict):
        return {1: payload["week"]}
    # Doğrudan gün haritası (taslak payload'ı): en az bir gün anahtarı varsa
    if any(k in payload for k in DAY_KEYS):
        return {1: payload}
    return {1: {}}


def write_program_weeks(cur, program_id: int, weeks: Dict[int, dict]) -> int:
    """workout_days + workout_exercises satırlarını yazar. Döner: yazılan gün sayısı."""
    from app.api.coach.routes import _flatten_day_to_exercises, _match_exercise_library, _fetchone_id

    written = 0
    for week_index in sorted(weeks):
        week = weeks[week_index] or {}
        day_order = 1
        for day_key in DAY_KEYS:
            day_value = week.get(day_key)
            if not day_value:
                continue
            if isinstance(day_value, dict):
                day_payload_json: Optional[str] = json.dumps(day_value)
                exercises_to_insert = _flatten_day_to_exercises(day_value)
            elif isinstance(day_value, list):
                day_payload_json = None
                exercises_to_insert = day_value
            else:
                continue
            cur.execute(
                """INSERT INTO workout_days (workout_program_id, day_of_week, order_index, week_index, day_payload)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (program_id, day_key, day_order, week_index, day_payload_json),
            )
            workout_day_id = _fetchone_id(cur.fetchone())
            for ex_order, ex in enumerate(exercises_to_insert, start=1):
                if not isinstance(ex, dict):
                    continue
                ex_name = ex.get("name") or ""
                matched = _match_exercise_library(cur, ex_name)
                lib_id = matched["id"] if matched else None
                resolved_name = matched["canonical_name"] if matched else ex_name
                cur.execute(
                    """INSERT INTO workout_exercises
                       (workout_day_id, exercise_name, sets, reps, notes, order_index, exercise_library_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (workout_day_id, resolved_name, ex.get("sets"), ex.get("reps") or "",
                     ex.get("notes") or "", ex_order, lib_id),
                )
            day_order += 1
            written += 1
    return written


def create_program_from_payload(
    cur,
    *,
    client_user_id: int,
    coach_user_id: int,
    title: str,
    payload: Any,
    is_active: bool,
) -> Tuple[int, int]:
    """workout_programs başlığı + haftalar. Döner: (program_id, total_weeks).

    is_active=True ise önce öğrencinin diğer aktif programları kapatılır.
    """
    weeks = normalize_weeks(payload)
    if is_active:
        cur.execute(
            "UPDATE workout_programs SET is_active = FALSE, updated_at = NOW() "
            "WHERE client_user_id = %s AND is_active = TRUE",
            (client_user_id,),
        )
    cur.execute(
        """INSERT INTO workout_programs (client_user_id, coach_user_id, title, is_active, created_at, updated_at)
           VALUES (%s, %s, %s, %s, NOW(), NOW()) RETURNING id""",
        (client_user_id, coach_user_id, title or "Coach Workout Program", bool(is_active)),
    )
    row = cur.fetchone()
    program_id = row["id"] if hasattr(row, "keys") else row[0]
    write_program_weeks(cur, program_id, weeks)
    return program_id, len(weeks)


def _flat_exercise(ex: dict) -> dict:
    out = {
        "name": ex.get("exercise_name") or "",
        "sets": ex.get("sets"),
        "reps": ex.get("reps") or "",
        "notes": ex.get("notes") or "",
    }
    if ex.get("gif_url"):
        out["gif_url"] = ex["gif_url"]
    if ex.get("exercise_library_id"):
        out["exercise_library_id"] = ex["exercise_library_id"]
    return out


def load_program_weeks(cur, program_id: int) -> Tuple[Dict[str, dict], Dict[str, list], int]:
    """Programın günlerini haftalara göre okur.

    Döner:
      weeks   {"1": {mon: day_payload|None, ...}, "2": ...}  — yapısal (day_payload varsa o,
              yoksa düz egzersiz listesinden kurulur) → admin editör
      week    1. haftanın DÜZ biçimi {mon: [exercise, ...]}     — geriye uyumluluk
      total_weeks
    """
    from app.api.client.workouts import build_day_payload_from_flat_exercises

    cur.execute(
        """SELECT id, day_of_week, order_index, week_index, day_payload
           FROM workout_days WHERE workout_program_id = %s
           ORDER BY week_index ASC, order_index ASC, id ASC""",
        (program_id,),
    )
    days = cur.fetchall() or []
    day_ids = [d["id"] for d in days]
    ex_by_day: Dict[int, List[dict]] = {}
    if day_ids:
        placeholders = ",".join(["%s"] * len(day_ids))
        cur.execute(
            f"""SELECT we.id, we.workout_day_id, we.exercise_name, we.sets, we.reps, we.notes,
                       we.order_index, we.exercise_library_id, el.gif_url
                FROM workout_exercises we
                LEFT JOIN exercise_library el ON el.id = we.exercise_library_id
                WHERE we.workout_day_id IN ({placeholders})
                ORDER BY we.workout_day_id ASC, we.order_index ASC, we.id ASC""",
            tuple(day_ids),
        )
        for ex in cur.fetchall() or []:
            ex_by_day.setdefault(ex["workout_day_id"], []).append(ex)

    weeks: Dict[str, dict] = {}
    for d in days:
        wk = str(d.get("week_index") or 1)
        day_key = d["day_of_week"]
        if day_key not in DAY_KEYS:
            continue
        week = weeks.setdefault(wk, {k: None for k in DAY_KEYS})
        exercises = ex_by_day.get(d["id"], [])
        payload = d.get("day_payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                payload = None
        if isinstance(payload, dict):
            week[day_key] = payload
        elif exercises:
            week[day_key] = build_day_payload_from_flat_exercises(exercises)
        # düz liste (eski `week` alanı) yalnız 1. hafta için
        if wk == "1":
            flat = week.setdefault("_flat", {})  # geçici; aşağıda ayrılır
            flat[day_key] = [_flat_exercise(e) for e in exercises]

    week1 = weeks.get("1", {})
    flat_week = {k: [] for k in DAY_KEYS}
    if "_flat" in week1:
        flat_week.update(week1.pop("_flat"))
    total_weeks = max(1, len(weeks)) if weeks else 1
    if not weeks:
        weeks = {"1": {k: None for k in DAY_KEYS}}
    return weeks, flat_week, total_weeks
