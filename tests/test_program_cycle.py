"""28. gün akışı — program döngüsü hesabı (DB gerektirmez)."""
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("AUTO_MIGRATE", "0")
os.environ.setdefault("SENTRY_DSN", "")


def test_compute_cycle_four_week_program():
    from app.services.program_cycle import compute_cycle

    start = date(2026, 9, 1)
    c = compute_cycle(start, 4, today=date(2026, 9, 1))  # 1. gün
    assert c["has_cycle_end"] and c["total_days"] == 28 and c["start_date"] == "2026-09-01"
    assert c["day_index"] == 1 and c["days_left"] == 28
    assert not c["ending_soon"] and not c["is_finished"]

    c = compute_cycle(start, 4, today=date(2026, 9, 25))  # 25. gün: henüz "bitmek üzere" değil
    assert c["day_index"] == 25 and c["days_left"] == 4 and not c["ending_soon"]

    c = compute_cycle(start, 4, today=date(2026, 9, 26))  # 26. gün: son 3 gün
    assert c["days_left"] == 3 and c["ending_soon"] and not c["is_finished"]

    c = compute_cycle(start, 4, today=date(2026, 9, 28))  # 28. gün: son gün
    assert c["day_index"] == 28 and c["days_left"] == 1 and c["ending_soon"]
    assert c["ends_on"] == "2026-09-28"

    c = compute_cycle(start, 4, today=date(2026, 9, 29))  # 29. gün: bitti
    assert c["is_finished"] and c["days_left"] == 0 and not c["ending_soon"] and c["day_index"] == 29

    c = compute_cycle(start, 4, today=date(2026, 11, 1))  # çok sonra: hâlâ bitti, day_index büyür
    assert c["is_finished"] and c["day_index"] == 62


def test_compute_cycle_single_week_template_never_ends():
    from app.services.program_cycle import compute_cycle

    c = compute_cycle(date(2026, 1, 1), 1, today=date(2026, 12, 1))
    assert c["has_cycle_end"] is False and c["is_finished"] is False
    assert c["days_left"] is None and c["ends_on"] is None and c["day_index"] == 335
    # None / 0 hafta → 1 hafta gibi davranır
    assert compute_cycle(date(2026, 1, 1), None, today=date(2026, 1, 2))["has_cycle_end"] is False


def test_compute_cycle_uses_istanbul_day_for_utc_timestamps():
    from app.services.program_cycle import compute_cycle

    # UTC 31 Ağustos 21:30 = Istanbul 1 Eylül 00:30 → program 1 Eylül'de başlar
    c = compute_cycle(datetime(2026, 8, 31, 21, 30), 4, today=date(2026, 9, 1))
    assert c["start_date"] == "2026-09-01" and c["day_index"] == 1
    # ISO string de kabul edilir
    c = compute_cycle("2026-09-01T10:00:00", 4, today=date(2026, 9, 2))
    assert c["day_index"] == 2
    # Gelecek tarihli created_at (saat kayması) negatif gün üretmez
    c = compute_cycle(date(2026, 9, 5), 4, today=date(2026, 9, 1))
    assert c["day_index"] == 1 and c["days_left"] == 28


def test_cycle_end_email_template_escapes_and_links():
    from app.services.email_service import render_program_cycle_end_email

    html = render_program_cycle_end_email(
        coach_name="Koç <b>", student_name="Ali & Veli", student_id=42,
        program_title="Push/Pull", days_left=2, is_finished=False,
        admin_url="https://admin.example",
    )
    assert "&lt;b&gt;" in html and "Ali &amp; Veli" in html
    assert "https://admin.example/students/42" in html and "2 gün içinde bitiyor" in html
    html = render_program_cycle_end_email(
        coach_name="", student_name="", student_id=7, program_title="",
        days_left=0, is_finished=True, admin_url="https://admin.example/",
    )
    assert "programını tamamladı" in html and "/students/7" in html
