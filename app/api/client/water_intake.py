"""Daily water intake tracking — simple glass counter."""
from fastapi import Depends
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


@router.post("/water-intake/add")
def add_water_glass(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Add one glass of water for today. Returns updated count."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """INSERT INTO daily_water_log (user_id, log_date, glasses)
           VALUES (%s, CURRENT_DATE, 1)
           ON CONFLICT (user_id, log_date)
           DO UPDATE SET glasses = daily_water_log.glasses + 1, updated_at = NOW()
           RETURNING glasses""",
        (current_user["id"],),
    )
    db.commit()
    return {"glasses": cur.fetchone()["glasses"]}


@router.post("/water-intake/remove")
def remove_water_glass(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Remove one glass (min 0). Returns updated count."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """INSERT INTO daily_water_log (user_id, log_date, glasses)
           VALUES (%s, CURRENT_DATE, 0)
           ON CONFLICT (user_id, log_date)
           DO UPDATE SET glasses = GREATEST(0, daily_water_log.glasses - 1), updated_at = NOW()
           RETURNING glasses""",
        (current_user["id"],),
    )
    db.commit()
    return {"glasses": cur.fetchone()["glasses"]}


@router.get("/water-intake/today")
def get_today_water(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Get today's water glass count + goal (from daily-targets water_liters)."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Current count
    cur.execute(
        "SELECT glasses FROM daily_water_log WHERE user_id = %s AND log_date = CURRENT_DATE",
        (current_user["id"],),
    )
    row = cur.fetchone()
    glasses = row["glasses"] if row else 0

    # Goal: water_liters from client profile → convert to glasses (1 glass = 250ml)
    cur.execute(
        "SELECT weight_kg FROM clients WHERE user_id = %s",
        (current_user["id"],),
    )
    client = cur.fetchone()
    if client and client["weight_kg"]:
        water_liters = round(max(2.0, min(4.0, float(client["weight_kg"]) * 0.035)), 1)
        goal_glasses = round(water_liters / 0.25)  # 250ml per glass
    else:
        goal_glasses = 8  # default

    return {
        "glasses": glasses,
        "goal_glasses": goal_glasses,
    }
