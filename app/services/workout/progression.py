"""Stage 7 — Progression / Microcycle.

Generates Weeks 2-4 from the Week 1 baseline. Pure deterministic — no LLM.

Strategy (per architecture decision):
  • Week 1: baseline           (rep range x sets x RIR olduğu gibi)
  • Week 2: add_reps           (rep range +2 — same load, more reps)
  • Week 3: add_load            (rep range -2, RIR -1 — load implicit up)
  • Week 4: deload             (sets -1, RIR +2, intensity backs off)

The "load" itself is never numeric in the schema (we don't know weights).
The progression communicates intent via rep range + RIR — the user/coach
adjusts kg based on those cues.

A WeeklyProgram is returned per week, ready to persist as 4 separate
workout_days collections (week_index column).
"""
from __future__ import annotations

import copy
import logging
import re
from typing import Literal

from .models import (
    AssembledExercise,
    AssembledSession,
    WeeklyProgram,
)

logger = logging.getLogger(__name__)

DeltaStrategy = Literal["baseline", "add_reps", "add_load", "deload"]


def _shift_rep_range(reps: str, delta_lower: int = 0, delta_upper: int = 0) -> str:
    """Shifts numeric rep tokens by delta. Examples:
        '8-10' shift(+2,+2) → '10-12'
        '5' shift(+2,+2) → '7'
        '8-10' shift(-2,-2) → '6-8'
    Non-numeric ranges ('Hata Noktası', '30 saniye') return as-is.
    """
    if not reps:
        return reps
    # Range form 'a-b'
    m = re.match(r"^(\d+)\s*-\s*(\d+)$", reps.strip())
    if m:
        lo = int(m.group(1)) + delta_lower
        hi = int(m.group(2)) + delta_upper
        lo = max(1, lo)
        hi = max(lo, hi)
        return f"{lo}-{hi}"
    # Single number
    m = re.match(r"^(\d+)$", reps.strip())
    if m:
        n = max(1, int(m.group(1)) + delta_upper)
        return str(n)
    # Time-based or qualitative (Hata Noktası, 30 saniye) — leave alone
    return reps


def _apply_baseline(session: AssembledSession) -> AssembledSession:
    return copy.deepcopy(session)


def _apply_add_reps(session: AssembledSession) -> AssembledSession:
    """Week 2: rep range +2 (both ends). Sets same. RIR same."""
    out = copy.deepcopy(session)
    for ex in out.exercises:
        ex.reps = _shift_rep_range(ex.reps, delta_lower=2, delta_upper=2)
        # Append week note to rationale (mobile uses it as a hint)
        if "Hafta 2" not in ex.rationale:
            ex.rationale = (ex.rationale + " — Hafta 2: +2 tekrar")[:80]
    return out


def _apply_add_load(session: AssembledSession) -> AssembledSession:
    """Week 3: rep range -2 (signals heavier load), RIR -1 (closer to failure).
    Total volume similar but load goes up."""
    out = copy.deepcopy(session)
    for ex in out.exercises:
        ex.reps = _shift_rep_range(ex.reps, delta_lower=-2, delta_upper=-2)
        ex.rir = max(0, ex.rir - 1)
        if "Hafta 3" not in ex.rationale:
            ex.rationale = (ex.rationale + " — Hafta 3: ağırlığı artır")[:80]
    return out


def _apply_deload(session: AssembledSession) -> AssembledSession:
    """Week 4: sets -1 per exercise (min 2), RIR +2 (back off intensity)."""
    out = copy.deepcopy(session)
    for ex in out.exercises:
        ex.sets = max(2, ex.sets - 1)
        ex.rir = min(5, ex.rir + 2)
        if "Deload" not in ex.rationale:
            ex.rationale = (ex.rationale + " — Hafta 4: deload")[:80]
    return out


_STRATEGY_FNS = {
    "baseline":  _apply_baseline,
    "add_reps":  _apply_add_reps,
    "add_load":  _apply_add_load,
    "deload":    _apply_deload,
}


def build_microcycle(base: WeeklyProgram) -> list[tuple[int, DeltaStrategy, WeeklyProgram]]:
    """Returns 4 (week_index, strategy, WeeklyProgram) tuples.

    Each WeeklyProgram is a deep copy of base with the strategy applied
    to every session's exercises. Persistence layer writes 4 × 7 = 28
    workout_days rows (week_index 1..4).
    """
    schedule: list[tuple[int, DeltaStrategy]] = [
        (1, "baseline"),
        (2, "add_reps"),
        (3, "add_load"),
        (4, "deload"),
    ]
    out = []
    for week_idx, strategy in schedule:
        fn = _STRATEGY_FNS[strategy]
        week_program = copy.deepcopy(base)
        week_program.sessions = [fn(s) for s in base.sessions]
        out.append((week_idx, strategy, week_program))
    return out
