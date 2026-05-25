"""Stage 2 — SplitPlanner.

Selects a WeeklySplit from the `split_templates` DB catalog given a
TrainingProfile. No LLM, no creativity — pure rule lookup:

  1. Filter by days_per_week (hard match)
  2. Filter by experience_lock — beginner CAN'T get PPL/Arnold even if
     they request 5 days; they'd get FB×5 instead.
  3. Filter by goal_match (any goal accepted if list is empty)
  4. Order by rank ASC, pick top
  5. Compute day assignment (which calendar days get workouts vs rest)

The catalog is config — adding a new split = one SQL INSERT, no code change.
"""
from __future__ import annotations

import logging
from typing import Any

from psycopg2.extras import RealDictCursor

from .models import SessionSpec, SplitFamily, TrainingProfile, WeeklySplit

logger = logging.getLogger(__name__)


class NoSuitableSplitError(Exception):
    """Catalog has no split matching the profile constraints."""


def _select_template_row(conn, profile: TrainingProfile) -> dict:
    """Query split_templates with profile's constraints.

    Falls back to a slightly relaxed search if the strict one returns
    nothing (e.g. unusual goal). Never injects a split the experience_lock
    forbids — that lock is the safety rail (no PPL for beginners).
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Strict match
    cur.execute(
        """
        SELECT * FROM split_templates
        WHERE active = TRUE
          AND days_per_week = %s
          AND (
            cardinality(experience_lock) = 0
            OR %s = ANY(experience_lock)
          )
          AND (
            cardinality(goal_match) = 0
            OR %s = ANY(goal_match)
          )
        ORDER BY rank ASC
        LIMIT 1
        """,
        (profile.days_per_week, profile.experience, profile.goal),
    )
    row = cur.fetchone()
    if row:
        return row

    # Relaxed match — drop goal constraint
    logger.warning(
        "split_planner: no strict match for days=%s exp=%s goal=%s — relaxing goal",
        profile.days_per_week, profile.experience, profile.goal,
    )
    cur.execute(
        """
        SELECT * FROM split_templates
        WHERE active = TRUE
          AND days_per_week = %s
          AND (
            cardinality(experience_lock) = 0
            OR %s = ANY(experience_lock)
          )
        ORDER BY rank ASC
        LIMIT 1
        """,
        (profile.days_per_week, profile.experience),
    )
    row = cur.fetchone()
    if row:
        return row

    # Last-resort fallback: find ANY split for this experience at +/-1 days
    logger.warning("split_planner: still no match — wide fallback")
    cur.execute(
        """
        SELECT * FROM split_templates
        WHERE active = TRUE
          AND %s = ANY(experience_lock) OR cardinality(experience_lock) = 0
        ORDER BY ABS(days_per_week - %s) ASC, rank ASC
        LIMIT 1
        """,
        (profile.experience, profile.days_per_week),
    )
    row = cur.fetchone()
    if not row:
        raise NoSuitableSplitError(
            f"split catalog empty for profile {profile.experience}/{profile.days_per_week}d"
        )
    return row


def _assign_day_indices(num_sessions: int) -> list[int]:
    """Map N sessions to calendar day indices (0=Mon ... 6=Sun) with
    even spacing for recovery. Returns indices in order.

    Patterns chosen for max muscle recovery:
        1 → [0]
        2 → [0,3]               Mon, Thu
        3 → [0,2,4]             Mon, Wed, Fri (classic 1-on-1-off)
        4 → [0,1,3,5]           Mon, Tue, Thu, Sat (split rest pattern)
        5 → [0,1,2,4,5]         Mon-Tue-Wed, Fri-Sat
        6 → [0,1,2,3,4,5]       Mon-Sat
        7 → [0,1,2,3,4,5,6]
    """
    layouts = {
        1: [0],
        2: [0, 3],
        3: [0, 2, 4],
        4: [0, 1, 3, 5],
        5: [0, 1, 2, 4, 5],
        6: [0, 1, 2, 3, 4, 5],
        7: [0, 1, 2, 3, 4, 5, 6],
    }
    return layouts.get(num_sessions, list(range(num_sessions)))


def plan_split(conn, profile: TrainingProfile) -> WeeklySplit:
    """Main entry. Returns a WeeklySplit populated with calendar-day-mapped
    SessionSpec objects."""
    row = _select_template_row(conn, profile)

    sessions_raw: list[dict[str, Any]] = row["day_sessions"]
    day_indices = _assign_day_indices(len(sessions_raw))

    sessions = [
        SessionSpec(
            name=s["name"],
            muscles=s["muscles"],
            day_index=day_indices[i],
        )
        for i, s in enumerate(sessions_raw)
    ]
    rest_days = sorted(set(range(7)) - set(day_indices))

    # Reflect chosen split id back on the profile for audit
    profile.recommended_split = row["split_id"]

    family: SplitFamily = row["family"]
    return WeeklySplit(
        split_id=row["split_id"],
        family=family,
        sessions=sessions,
        rest_day_indices=rest_days,
        rationale=row.get("rationale") or "",
    )
