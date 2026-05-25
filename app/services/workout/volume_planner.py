"""Stage 3 — VolumePlanner.

Weekly + per-session set target math. Pure deterministic. No LLM.

Strategy (per architecture decision):
  * Conservative — target stays between MEV and MAV; MRV target = NEVER.
  * Reasoning: real users have imperfect sleep/nutrition/adherence.
  * Default base target = MAV - 2 (median-low band).
  * Priority muscle = MAV (caller's explicit ask, not stretched to MRV).
  * goal modifier: fat_loss / endurance / strength → -1 or -2 offset.

Per-session distribution: weekly muscle volume divided by how many
sessions touch that muscle, with min 2 sets / max 6 sets per
muscle / session clamping.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

from .models import (
    MuscleSetTarget,
    SessionTargets,
    TrainingProfile,
    VolumeTargets,
    WeeklySplit,
)

logger = logging.getLogger(__name__)

_RULES_PATH = Path(__file__).parent / "rules" / "volume.json"
_RULES = json.loads(_RULES_PATH.read_text(encoding="utf-8"))

_BANDS: dict[str, dict[str, list[int]]] = _RULES["bands"]
_GOAL_MOD: dict[str, dict] = _RULES["goal_modifiers"]


def _band(muscle: str, experience: str) -> tuple[int, int, int]:
    """Returns (MEV, MAV, MRV) for muscle x experience.

    Falls back to the chest band when muscle is unknown — defensive,
    happens for new muscles added without volume.json update.
    """
    bands = _BANDS.get(muscle) or _BANDS["chest"]
    band_for_exp = bands.get(experience) or bands["intermediate"]
    return tuple(band_for_exp)  # type: ignore


def _target_weekly_sets(profile: TrainingProfile, muscle: str) -> int:
    """How many weekly sets for this muscle for this user?"""
    mev, mav, mrv = _band(muscle, profile.experience)

    if muscle in profile.priority_muscles:
        target = mav            # priority gets MAV
    else:
        target = max(mev, mav - 2)   # conservative — MAV minus 2

    # Goal modifier
    mod = _GOAL_MOD.get(profile.goal, {}).get("target_offset", 0)
    target += mod

    # Hard clamps — never below MEV, never above MAV-1
    target = max(mev, target)
    target = min(mav, target)
    return int(target)


def _muscles_per_session(split: WeeklySplit) -> dict[str, list[int]]:
    """For each muscle, which session indices touch it?"""
    out: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(split.sessions):
        for m in s.muscles:
            out[m].append(i)
    return out


def _distribute_across_sessions(
    weekly: dict[str, int],
    split: WeeklySplit,
    profile: TrainingProfile,
) -> list[SessionTargets]:
    """Convert weekly targets → per-session targets."""
    touches = _muscles_per_session(split)

    per_session_per_muscle: dict[int, dict[str, int]] = defaultdict(dict)
    for muscle, weekly_sets in weekly.items():
        session_idxs = touches.get(muscle, [])
        if not session_idxs:
            continue
        # even split
        per = max(2, weekly_sets // len(session_idxs))
        # carry the remainder onto first sessions
        remainder = weekly_sets - per * len(session_idxs)
        for i, sidx in enumerate(session_idxs):
            assigned = per + (1 if i < remainder else 0)
            assigned = min(6, max(2, assigned))   # clamp 2..6 per muscle per session
            per_session_per_muscle[sidx][muscle] = assigned

    targets: list[SessionTargets] = []
    for i, s in enumerate(split.sessions):
        per_muscle = per_session_per_muscle.get(i, {})
        rows = [
            MuscleSetTarget(muscle=m, sets=n)
            for m, n in per_muscle.items()
            if m in s.muscles  # don't include muscles the split doesn't expect here
        ]
        # exercise count hint = sum_sets / 3 (average 3 sets / exercise), clamped 5..8
        total = sum(r.sets for r in rows)
        ex_hint = max(5, min(8, round(total / 3)))
        targets.append(SessionTargets(
            session_name=s.name,
            day_index=s.day_index,
            per_muscle_sets=rows,
            total_set_budget=total,
            exercise_count_hint=ex_hint,
        ))
    return targets


# ──────────────────────────────────────────────────────────────────────
#  Public
# ──────────────────────────────────────────────────────────────────────
def plan_volume(profile: TrainingProfile, split: WeeklySplit) -> VolumeTargets:
    """Compute weekly + per-session set distribution.

    All math is deterministic. Same profile + split → same targets.
    """
    weekly = {
        muscle: _target_weekly_sets(profile, muscle)
        for muscle in {m for s in split.sessions for m in s.muscles}
    }
    sessions = _distribute_across_sessions(weekly, split, profile)
    return VolumeTargets(weekly_per_muscle=weekly, sessions=sessions)
