"""Badge awarding service — call after user actions to check and award badges."""
from app.core.database import get_db


def award_badge(user_id: int, badge_id: str) -> bool:
    """Award a badge to user. Returns True if newly awarded, False if already had."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_badges (user_id, badge_id) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING id",
            (user_id, badge_id),
        )
        result = cur.fetchone()
        conn.commit()
        return result is not None
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def check_and_award(user_id: int, trigger: str, db=None):
    """Check trigger-based badges and award if earned. Call from API endpoints."""
    close_conn = False
    if db is None:
        db = get_db()
        close_conn = True

    try:
        cur = db.cursor()
        newly_earned = []

        if trigger == 'login':
            if _award(cur, user_id, 'first_login'):
                newly_earned.append('first_login')

        elif trigger == 'onboarding_complete':
            if _award(cur, user_id, 'onboarding_complete'):
                newly_earned.append('onboarding_complete')

        elif trigger == 'coach_assigned':
            if _award(cur, user_id, 'first_coach'):
                newly_earned.append('first_coach')

        elif trigger == 'ai_coach_purchased':
            if _award(cur, user_id, 'ai_coach'):
                newly_earned.append('ai_coach')

        elif trigger == 'workout_completed':
            if _award(cur, user_id, 'first_workout'):
                newly_earned.append('first_workout')
            # Check streaks
            _check_streak_badges(cur, user_id, newly_earned)

        elif trigger == 'meal_photo_sent':
            if _award(cur, user_id, 'first_meal_photo'):
                newly_earned.append('first_meal_photo')

        elif trigger == 'all_meals_logged':
            if _award(cur, user_id, 'all_meals_logged'):
                newly_earned.append('all_meals_logged')

        elif trigger == 'weight_logged':
            if _award(cur, user_id, 'first_weighin'):
                newly_earned.append('first_weighin')

        elif trigger == 'measurement_logged':
            if _award(cur, user_id, 'first_measurement'):
                newly_earned.append('first_measurement')

        elif trigger == 'message_sent':
            if _award(cur, user_id, 'first_message'):
                newly_earned.append('first_message')

        elif trigger == 'checkin_complete':
            if _award(cur, user_id, 'checkin_complete'):
                newly_earned.append('checkin_complete')

        elif trigger == 'photo_uploaded':
            if _award(cur, user_id, 'transformation'):
                newly_earned.append('transformation')

        # Check membership duration badges
        _check_membership_badges(cur, user_id, newly_earned)

        db.commit()
        return newly_earned

    except Exception:
        db.rollback()
        return []
    finally:
        if close_conn:
            db.close()


def _award(cur, user_id, badge_id):
    cur.execute(
        "INSERT INTO user_badges (user_id, badge_id) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING id",
        (user_id, badge_id),
    )
    return cur.fetchone() is not None


def _check_streak_badges(cur, user_id, newly_earned):
    """Check workout streak and award streak badges."""
    # Simple: count consecutive days with completed workouts (mock for now)
    # In production, query workout completion logs
    cur.execute("SELECT COUNT(*) FROM user_badges WHERE user_id = %s AND badge_id = 'first_workout'", (user_id,))
    # For now, we don't have a workout_logs table, so skip streak calculation
    pass


def _check_membership_badges(cur, user_id, newly_earned):
    """Award membership duration badges."""
    cur.execute("SELECT created_at FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    if not row:
        return

    from datetime import datetime
    created = row[0] if not isinstance(row, dict) else row.get("created_at")
    if created is None:
        return

    days = (datetime.utcnow() - created).days

    if days >= 7:
        if _award(cur, user_id, 'member_7'):
            newly_earned.append('member_7')
    if days >= 30:
        if _award(cur, user_id, 'member_30'):
            newly_earned.append('member_30')
    if days >= 90:
        if _award(cur, user_id, 'member_90'):
            newly_earned.append('member_90')
