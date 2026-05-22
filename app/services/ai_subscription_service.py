"""AI Coach subscription + quota service.

Provides three responsibilities:
  1. **Tier lookup**: which tier is the user on right now? (None if free)
  2. **Quota check + increment**: can the user perform this AI action, and
     if yes, atomically increment the monthly counter.
  3. **Mock subscription creation**: for development/test until Apple IAP
     DUNS verification clears.

DB tables: ai_subscriptions, ai_quota_usage (migration 047).

Apple IAP (StoreKit) integration lives in a separate endpoint once DUNS is
done — that endpoint will create rows with status='active' and a real
apple_transaction_id; mock mode uses status='mock'. Both are treated the
same by lookup logic, so the rest of the codebase doesn't need to care.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
#  Tier definitions — single source of truth
# ──────────────────────────────────────────────────────────────────────
TIER_LIMITS: dict[str, dict[str, int]] = {
    "starter": {
        "chat":           30,
        "meal_analysis":  5,
        "body_analysis":  0,
        "workout_regen":  0,
    },
    "pro": {
        "chat":           500,
        "meal_analysis":  30,
        "body_analysis":  10,
        "workout_regen":  4,
    },
    "elite": {
        "chat":           10_000,  # fair-use cap
        "meal_analysis":  100_000,
        "body_analysis":  100_000,
        "workout_regen":  100_000,
    },
}

QUOTA_TYPES = ("chat", "meal_analysis", "body_analysis", "workout_regen")


# ──────────────────────────────────────────────────────────────────────
#  Internal helpers
# ──────────────────────────────────────────────────────────────────────
def _month_key(at: Optional[datetime] = None) -> str:
    """Returns 'YYYY-MM' bucket key in UTC."""
    at = at or datetime.now(timezone.utc)
    return at.strftime("%Y-%m")


# ──────────────────────────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────────────────────────
def get_active_tier(conn, user_id: int) -> Optional[str]:
    """Returns the user's active AI Coach tier ('starter'|'pro'|'elite') or
    None if no active subscription. 'mock' status is treated as active for
    dev/test mode.
    """
    if not user_id:
        return None
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT tier
        FROM ai_subscriptions
        WHERE user_id = %s
          AND status IN ('active', 'mock')
          AND expires_at > NOW()
        ORDER BY expires_at DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cur.fetchone()
    return row["tier"] if row else None


def get_subscription_status(conn, user_id: int) -> dict:
    """Returns full subscription + quota status for a user.

    {
      "tier": "pro" | "starter" | "elite" | None,
      "billing_period": "monthly" | "yearly" | None,
      "expires_at": iso8601 | None,
      "status": "active" | "mock" | None,
      "limits": {"chat": 500, "meal_analysis": 30, ...} | {},
      "used": {"chat": 12, "meal_analysis": 3, ...},
      "remaining": {"chat": 488, "meal_analysis": 27, ...},
    }
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT tier, billing_period, status, expires_at
        FROM ai_subscriptions
        WHERE user_id = %s
          AND status IN ('active', 'mock')
          AND expires_at > NOW()
        ORDER BY expires_at DESC
        LIMIT 1
        """,
        (user_id,),
    )
    sub = cur.fetchone()

    if not sub:
        return {
            "tier": None,
            "billing_period": None,
            "expires_at": None,
            "status": None,
            "limits": {},
            "used": {q: 0 for q in QUOTA_TYPES},
            "remaining": {q: 0 for q in QUOTA_TYPES},
        }

    tier = sub["tier"]
    limits = TIER_LIMITS.get(tier, {}).copy()

    # Used counters for current month
    mk = _month_key()
    cur.execute(
        """
        SELECT quota_type, used_count
        FROM ai_quota_usage
        WHERE user_id = %s AND month_key = %s
        """,
        (user_id, mk),
    )
    used_rows = cur.fetchall()
    used = {q: 0 for q in QUOTA_TYPES}
    for r in used_rows:
        used[r["quota_type"]] = r["used_count"]

    remaining = {q: max(limits.get(q, 0) - used.get(q, 0), 0) for q in QUOTA_TYPES}

    return {
        "tier": tier,
        "billing_period": sub["billing_period"],
        "expires_at": sub["expires_at"].isoformat() if sub["expires_at"] else None,
        "status": sub["status"],
        "limits": limits,
        "used": used,
        "remaining": remaining,
    }


def check_quota(conn, user_id: int, quota_type: str) -> tuple[bool, str]:
    """Check whether the user can consume one unit of `quota_type`.

    Returns (allowed, reason).
      allowed=True, reason='ok'
      allowed=False, reason='no_subscription' | 'tier_disallowed' | 'limit_reached'
    Does NOT mutate the counter — call increment_quota after the action
    succeeds.
    """
    if quota_type not in QUOTA_TYPES:
        return False, f"invalid_quota_type:{quota_type}"

    tier = get_active_tier(conn, user_id)
    if not tier:
        return False, "no_subscription"

    limit = TIER_LIMITS.get(tier, {}).get(quota_type, 0)
    if limit <= 0:
        return False, "tier_disallowed"

    cur = conn.cursor(cursor_factory=RealDictCursor)
    mk = _month_key()
    cur.execute(
        """
        SELECT used_count
        FROM ai_quota_usage
        WHERE user_id = %s AND month_key = %s AND quota_type = %s
        """,
        (user_id, mk, quota_type),
    )
    row = cur.fetchone()
    used = row["used_count"] if row else 0

    if used >= limit:
        return False, "limit_reached"
    return True, "ok"


def increment_quota(conn, user_id: int, quota_type: str, delta: int = 1) -> None:
    """Atomically increment the user's monthly quota counter. Idempotent
    upsert. Call AFTER the AI action succeeded — don't burn quota on
    failures.
    """
    if quota_type not in QUOTA_TYPES:
        return
    cur = conn.cursor()
    mk = _month_key()
    cur.execute(
        """
        INSERT INTO ai_quota_usage (user_id, month_key, quota_type, used_count, last_used_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (user_id, month_key, quota_type)
        DO UPDATE SET
            used_count = ai_quota_usage.used_count + EXCLUDED.used_count,
            last_used_at = NOW(),
            updated_at = NOW()
        """,
        (user_id, mk, quota_type, delta),
    )
    conn.commit()


def create_mock_subscription(
    conn,
    user_id: int,
    tier: str,
    billing_period: str = "monthly",
) -> dict:
    """Create a 'mock' subscription for dev/test. Replaces any existing
    active sub for the same user (upgrade/downgrade).

    Returns the new subscription row as dict.
    """
    if tier not in TIER_LIMITS:
        raise ValueError(f"invalid tier: {tier}")
    if billing_period not in ("monthly", "yearly"):
        raise ValueError(f"invalid billing_period: {billing_period}")

    # End-date: +30 days monthly, +365 days yearly
    days = 365 if billing_period == "yearly" else 30

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Cancel existing active sub (atomic upgrade/downgrade)
    cur.execute(
        """
        UPDATE ai_subscriptions
        SET status = 'canceled', canceled_at = NOW(), updated_at = NOW()
        WHERE user_id = %s AND status IN ('active', 'mock')
        """,
        (user_id,),
    )

    cur.execute(
        """
        INSERT INTO ai_subscriptions
            (user_id, tier, billing_period, status, started_at, expires_at)
        VALUES
            (%s, %s, %s, 'mock', NOW(), NOW() + (%s || ' days')::INTERVAL)
        RETURNING id, user_id, tier, billing_period, status, started_at, expires_at
        """,
        (user_id, tier, billing_period, str(days)),
    )
    new_row = cur.fetchone()
    conn.commit()

    logger.info("ai_sub: created mock user=%s tier=%s period=%s", user_id, tier, billing_period)
    return {
        "id": new_row["id"],
        "user_id": new_row["user_id"],
        "tier": new_row["tier"],
        "billing_period": new_row["billing_period"],
        "status": new_row["status"],
        "started_at": new_row["started_at"].isoformat() if new_row["started_at"] else None,
        "expires_at": new_row["expires_at"].isoformat() if new_row["expires_at"] else None,
    }


def cancel_subscription(conn, user_id: int) -> bool:
    """Cancel user's active AI subscription. Returns True if a sub was canceled."""
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE ai_subscriptions
        SET status = 'canceled', canceled_at = NOW(), updated_at = NOW()
        WHERE user_id = %s AND status IN ('active', 'mock')
        """,
        (user_id,),
    )
    affected = cur.rowcount
    conn.commit()
    return affected > 0
