"""KVKK veri taşınabilirliği: kullanıcının kendi verisini JSON olarak toplar.

Tablo/kolon eksikse (lokal DB prod'un gerisinde) o tablo atlanır; şema
farkları dışa aktarmayı bozmaz.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_SENSITIVE_USER_COLUMNS = {
    "password_hash", "remember_token", "remember_token_expires_at", "otp_code",
    "otp_expires_at", "email_verification_token", "provider_user_id",
}

# (tablo, kullanıcı kolonu)
_USER_TABLES = [
    ("clients", "user_id"),
    ("client_onboarding", "user_id"),
    ("body_measurements", "user_id"),
    ("body_form_photos", "client_user_id"),
    ("body_form_analyses", "client_user_id"),
    ("meal_photos", "client_user_id"),
    ("daily_water_log", "user_id"),
    ("workout_sessions", "user_id"),
    ("user_badges", "user_id"),
    ("subscriptions", "client_user_id"),
    ("ai_subscriptions", "user_id"),
    ("ai_quota_usage", "user_id"),
    ("workout_programs", "client_user_id"),
    ("nutrition_programs", "client_user_id"),
    ("cardio_programs", "client_user_id"),
    ("activity_log", "client_user_id"),
    ("coach_reviews", "client_user_id"),
    ("form_analysis_settings", "client_user_id"),
    ("conversations", "client_user_id"),
]

_CHILD_QUERIES = {
    "workout_days": (
        "SELECT * FROM workout_days WHERE workout_program_id IN "
        "(SELECT id FROM workout_programs WHERE client_user_id = %s) ORDER BY id"
    ),
    "workout_exercises": (
        "SELECT * FROM workout_exercises WHERE workout_day_id IN "
        "(SELECT id FROM workout_days WHERE workout_program_id IN "
        "(SELECT id FROM workout_programs WHERE client_user_id = %s)) ORDER BY id"
    ),
    "nutrition_meals": (
        "SELECT * FROM nutrition_meals WHERE nutrition_program_id IN "
        "(SELECT id FROM nutrition_programs WHERE client_user_id = %s) ORDER BY id"
    ),
    "cardio_sessions": (
        "SELECT * FROM cardio_sessions WHERE cardio_program_id IN "
        "(SELECT id FROM cardio_programs WHERE client_user_id = %s) ORDER BY id"
    ),
    "messages": (
        "SELECT * FROM messages WHERE conversation_id IN "
        "(SELECT id FROM conversations WHERE client_user_id = %s) ORDER BY id"
    ),
}


def _rows(conn, sql: str, params: tuple) -> Optional[List[Dict[str, Any]]]:
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return [dict(r) for r in (cur.fetchall() or [])]
    except Exception as e:
        # Tablo/kolon yok → transaction aborted olur; temizle ve atla
        try:
            conn.rollback()
        except Exception:
            pass
        logger.info("data_export: atlandı (%s): %s", sql[:60], type(e).__name__)
        return None


def build_export(conn, user_id: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "note": "FithubPoint hesabınıza ait kişisel verilerin kopyası (KVKK m.11).",
        "user": None,
        "tables": {},
    }
    users = _rows(conn, "SELECT * FROM users WHERE id = %s", (user_id,))
    if users:
        out["user"] = {k: v for k, v in users[0].items() if k not in _SENSITIVE_USER_COLUMNS}

    for table, col in _USER_TABLES:
        rows = _rows(conn, f"SELECT * FROM {table} WHERE {col} = %s ORDER BY 1", (user_id,))
        if rows is not None:
            out["tables"][table] = rows
    for table, sql in _CHILD_QUERIES.items():
        rows = _rows(conn, sql, (user_id,))
        if rows is not None:
            out["tables"][table] = rows
    out["table_count"] = len(out["tables"])
    return out
