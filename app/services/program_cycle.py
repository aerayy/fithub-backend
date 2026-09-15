"""Antrenman programı döngüsü (4 haftalık mikrosüvel) — hesap + döngü sonu bildirimi.

v3 programlar 4 hafta × 7 gün = 28 günlük bir döngüdür (workout_days.week_index
1..4). Tek haftalık şablonlar (v2 / manuel koç programı) her hafta tekrar eder;
onların bir "bitişi" yoktur (has_cycle_end=False).

- compute_cycle(): saf hesap, test edilebilir. "Bugün" Europe/Istanbul'a göre
  alınır (tüm kullanıcılar TR'de); UTC gece yarısı kaymasını önler.
- notify_cycle_end(): döngü son 3 güne girince ya da bitince, program başına
  BİR kez: öğrenciye push, gerçek koça e-posta, aktivite logu. İdempotentlik
  workout_programs.cycle_end_notified_at (migration 065) ile.
- Tetikleyiciler: (1) saatlik cron → POST /admin/maintenance/notify-program-endings,
  (2) öğrenci uygulamayı açınca GET /client/workouts/active (arka plan iş parçacığı).
"""
from __future__ import annotations

import logging
import os
import threading
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

AI_COACH_USER_ID = 60
ENDING_SOON_DAYS = 3
TZ = ZoneInfo("Europe/Istanbul")
ADMIN_PANEL_URL = os.getenv("ADMIN_PANEL_URL", "https://fithub-admin-nwtg.onrender.com").rstrip("/")


def local_today() -> date:
    return datetime.now(TZ).date()


def _as_local_date(value) -> Optional[date]:
    """DB timestamp'i (naive = UTC varsayımı) Istanbul tarihine çevirir."""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(TZ).date()
    if isinstance(value, date):
        return value
    try:
        dt = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        return _as_local_date(dt)
    except Exception:
        return None


def compute_cycle(created_at, total_weeks, today: Optional[date] = None) -> dict:
    """Programın döngü durumu.

    Dönen alanlar:
      has_cycle_end  çok haftalı program mı (tek haftalık şablon sonsuz tekrar eder)
      total_weeks    hafta sayısı (workout_days.week_index farklı değer sayısı)
      total_days     hafta × 7
      start_date     ISO (Istanbul günü) — takvim şeridinin ilk günü
      day_index      bugün programın kaçıncı günü (1'den başlar, total_days'i aşabilir)
      days_left      kalan gün (bugün dahil; bitince 0) — tek haftalıkta None
      is_finished    day_index > total_days
      ending_soon    bitmedi ama son ENDING_SOON_DAYS gün içinde
      ends_on        son program günü (ISO) — tek haftalıkta None
    """
    today = today or local_today()
    weeks = max(1, int(total_weeks or 1))
    start = _as_local_date(created_at) or today
    days_since = max(0, (today - start).days)
    total_days = weeks * 7
    out = {
        "has_cycle_end": weeks >= 2,
        "total_weeks": weeks,
        "total_days": total_days,
        "start_date": start.isoformat(),
        "day_index": days_since + 1,
        "days_left": None,
        "is_finished": False,
        "ending_soon": False,
        "ends_on": None,
    }
    if weeks < 2:
        return out
    days_left = max(0, total_days - days_since)
    is_finished = days_since >= total_days
    out.update({
        "days_left": days_left,
        "is_finished": is_finished,
        "ending_soon": (not is_finished) and days_left <= ENDING_SOON_DAYS,
        "ends_on": (start + timedelta(days=total_days - 1)).isoformat(),
    })
    return out


def program_weeks(cur, program_id: int) -> int:
    cur.execute(
        "SELECT COUNT(DISTINCT week_index)::int AS w FROM workout_days WHERE workout_program_id = %s",
        (program_id,),
    )
    row = cur.fetchone()
    if not row:
        return 1
    w = row["w"] if hasattr(row, "get") else row[0]
    return max(1, int(w or 1))


def select_pending_programs(cur, *, limit: int = 200) -> list[dict]:
    """Döngü sonu bildirimi bekleyen aktif programlar (henüz işaretlenmemiş).

    SQL ön eleme UTC gününe göre; kesin karar compute_cycle (Istanbul) ile.
    """
    cur.execute(
        """SELECT wp.id AS program_id, wp.client_user_id, wp.coach_user_id, wp.title,
                  wp.created_at, w.weeks
           FROM workout_programs wp
           JOIN LATERAL (
               SELECT COUNT(DISTINCT week_index)::int AS weeks
               FROM workout_days WHERE workout_program_id = wp.id
           ) w ON TRUE
           WHERE wp.is_active = TRUE
             AND wp.cycle_end_notified_at IS NULL
             AND wp.created_at <= NOW() - INTERVAL '10 days'
             AND w.weeks >= 2
             AND (CURRENT_DATE - wp.created_at::date) >= (w.weeks * 7 - %s)
           ORDER BY wp.created_at ASC
           LIMIT %s""",
        (ENDING_SOON_DAYS, limit),
    )
    out = []
    for r in cur.fetchall() or []:
        r = dict(r)
        cyc = compute_cycle(r["created_at"], r["weeks"])
        if not (cyc["ending_soon"] or cyc["is_finished"]):
            continue
        out.append({
            "program_id": r["program_id"],
            "client_user_id": r["client_user_id"],
            "coach_user_id": r["coach_user_id"],
            "title": r.get("title") or "",
            "kind": "ai" if r["coach_user_id"] in (None, AI_COACH_USER_ID) else "coach",
            "days_left": cyc["days_left"],
            "is_finished": cyc["is_finished"],
        })
    return out


def notify_cycle_end(program_id: int) -> Optional[dict]:
    """Program başına bir kez bildirir. None → zaten bildirilmiş / uygun değil.

    Önce işaret atılır (claim), sonra bildirimler gönderilir; böylece cron ile
    uygulama açılışı aynı anda tetiklense de tek bildirim gider.
    """
    from psycopg2.extras import RealDictCursor
    from app.core.database import _get_pool

    pool = _get_pool()
    conn = pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """UPDATE workout_programs
               SET cycle_end_notified_at = NOW()
               WHERE id = %s AND is_active = TRUE AND cycle_end_notified_at IS NULL
               RETURNING id, client_user_id, coach_user_id, title, created_at""",
            (program_id,),
        )
        prog = cur.fetchone()
        if not prog:
            conn.rollback()
            return None
        cycle = compute_cycle(prog["created_at"], program_weeks(cur, program_id))
        if not cycle["has_cycle_end"]:
            conn.rollback()  # tek haftalık şablon: bitiş yok, işaret atma
            return None
        cur.execute(
            """SELECT COALESCE(o.full_name, u.full_name, u.email) AS student_name
               FROM users u LEFT JOIN client_onboarding o ON o.user_id = u.id
               WHERE u.id = %s""",
            (prog["client_user_id"],),
        )
        srow = cur.fetchone()
        student_name = (srow or {}).get("student_name") or "Öğrenci"
        is_ai = prog["coach_user_id"] in (None, AI_COACH_USER_ID)
        coach = None
        if not is_ai:
            # Öğrenci hâlâ bu koça atalıysa e-posta gider.
            cur.execute(
                """SELECT u.email, COALESCE(u.full_name, u.email) AS name
                   FROM users u
                   JOIN clients c ON c.user_id = %s AND c.assigned_coach_id = u.id
                   WHERE u.id = %s""",
                (prog["client_user_id"], prog["coach_user_id"]),
            )
            coach = cur.fetchone()
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("notify_cycle_end: db error program=%s", program_id)
        return None
    finally:
        pool.putconn(conn)

    result = {
        "program_id": program_id,
        "client_user_id": prog["client_user_id"],
        "coach_user_id": prog["coach_user_id"],
        "kind": "ai" if is_ai else "coach",
        "is_finished": cycle["is_finished"],
        "days_left": cycle["days_left"],
        "push_sent": False,
        "coach_email_sent": False,
    }
    finished = cycle["is_finished"]
    days_left = cycle["days_left"] or 0

    # Öğrenciye push (Firebase kimliği yoksa servis sessizce atlar)
    try:
        from app.services.push_notification import send_notification

        if finished:
            title = "Programın tamamlandı"
            body = (
                "4 haftalık döngünü bitirdin. Yeni döngünü oluşturmak için dokun."
                if is_ai else
                "4 haftalık programını tamamladın. Koçuna haber verdik, yeni programın hazırlanıyor."
            )
        else:
            title = "Programının son günü" if days_left == 1 else f"Programının son {days_left} günü"
            body = (
                "Döngün bitince yeni programını tek dokunuşla oluşturabileceksin."
                if is_ai else
                "Koçuna haber verdik; yeni programın hazır olunca burada göreceksin."
            )
        send_notification(
            prog["client_user_id"], title, body,
            {"type": "program_cycle_end", "program_type": "workout"},
        )
        result["push_sent"] = True
    except Exception:
        logger.exception("notify_cycle_end: push failed program=%s", program_id)

    # Gerçek koça e-posta (Resend yoksa no-op)
    if coach and coach.get("email"):
        try:
            from app.services.email_service import render_program_cycle_end_email, send_email

            subject = (
                f"{student_name} adlı öğrencinin programı tamamlandı"
                if finished else
                f"{student_name} adlı öğrencinin programı {days_left} gün içinde bitiyor"
            )
            html = render_program_cycle_end_email(
                coach_name=coach.get("name") or "",
                student_name=student_name,
                student_id=prog["client_user_id"],
                program_title=prog.get("title") or "",
                days_left=days_left,
                is_finished=finished,
                admin_url=ADMIN_PANEL_URL,
            )
            resp = send_email(to=coach["email"], subject=subject, html=html)
            result["coach_email_sent"] = not (isinstance(resp, dict) and resp.get("skipped"))
        except Exception:
            logger.exception("notify_cycle_end: coach email failed program=%s", program_id)

    # Koç panosu aktivite akışı
    try:
        from app.services.activity_log import log_activity

        log_activity(
            prog["client_user_id"],
            None if is_ai else prog["coach_user_id"],
            "program_cycle_end",
            "Program döngüsü tamamlandı" if finished else f"Program döngüsünün son {days_left} günü",
            (prog.get("title") or "Antrenman programı") + " — 4 haftalık döngü",
        )
    except Exception:
        pass

    logger.info("program cycle end notified program=%s kind=%s finished=%s", program_id, result["kind"], finished)
    return result


def notify_cycle_end_async(program_id: int) -> None:
    """İstek yolunu bekletmeden arka planda bildir (idempotent)."""
    def _run():
        try:
            notify_cycle_end(program_id)
        except Exception:
            logger.exception("notify_cycle_end_async failed program=%s", program_id)

    threading.Thread(target=_run, name=f"cycle-end-{program_id}", daemon=True).start()
