"""Activity log service — records student actions for coach dashboard."""
from app.core.database import _get_pool


def log_activity(
    client_user_id: int,
    coach_user_id: int | None,
    action_type: str,
    title: str,
    detail: str = "",
    photo_url: str | None = None,
):
    """Write an activity log entry. Fire-and-forget — never raises."""
    try:
        pool = _get_pool()
        conn = pool.getconn()
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO activity_log (client_user_id, coach_user_id, action_type, title, detail, photo_url)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (client_user_id, coach_user_id, action_type, title, detail, photo_url),
            )
            conn.commit()
        finally:
            pool.putconn(conn)
    except Exception:
        pass
