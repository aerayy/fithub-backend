"""Koç tarafı beslenme programı yazıcı — manuel kayıt, taslak atama ve zamanlanmış
taslak aktivasyonu aynı yolu kullanır (nutrition_programs + nutrition_meals).

Payload: {"week": {"mon": [meal, ...], ...}, "supplements": [...]} veya doğrudan gün haritası.
meal = {"items": [...], "time": "08:00"}; meal_type = "<day>:<n>. Öğün" (uygulama bu biçimi bekler).
"""
from __future__ import annotations

import json
from typing import Any, Tuple

DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _split_payload(payload: Any) -> Tuple[dict, list]:
    if not isinstance(payload, dict):
        return {}, []
    if isinstance(payload.get("week"), dict):
        return payload["week"], list(payload.get("supplements") or [])
    if any(k in payload for k in DAY_KEYS):
        return payload, list(payload.get("supplements") or [])
    return {}, list(payload.get("supplements") or [])


def create_nutrition_program_from_payload(
    cur,
    *,
    client_user_id: int,
    coach_user_id: int,
    title: str,
    payload: Any,
    is_active: bool,
) -> int:
    """nutrition_programs başlığı + nutrition_meals satırları. Döner: program id.

    is_active=True ise öğrencinin diğer aktif beslenme programları önce kapatılır.
    """
    week, supplements = _split_payload(payload)
    if is_active:
        cur.execute(
            "UPDATE nutrition_programs SET is_active = FALSE, updated_at = NOW() "
            "WHERE client_user_id = %s AND is_active = TRUE",
            (client_user_id,),
        )
    cur.execute(
        """INSERT INTO nutrition_programs (client_user_id, coach_user_id, title, is_active, supplements)
           VALUES (%s, %s, %s, %s, %s::jsonb) RETURNING id""",
        (client_user_id, coach_user_id, title or "Coach Nutrition Program", bool(is_active),
         json.dumps(supplements or [])),
    )
    row = cur.fetchone()
    program_id = row["id"] if hasattr(row, "keys") else row[0]
    order_counter = 0
    for day_key in DAY_KEYS:
        day_meals = week.get(day_key) or []
        if not isinstance(day_meals, list):
            continue
        for idx, m in enumerate(day_meals, start=1):
            if not isinstance(m, dict):
                continue
            order_counter += 1
            cur.execute(
                """INSERT INTO nutrition_meals (nutrition_program_id, meal_type, content, order_index, planned_time)
                   VALUES (%s, %s, %s, %s, %s)""",
                (program_id, f"{day_key}:{idx}. Öğün", json.dumps(m.get("items") or []),
                 order_counter, m.get("time") or None),
            )
    return program_id
