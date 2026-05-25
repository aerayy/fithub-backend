"""Stage 6 — Validator + Repair.

Runs structural checks on the assembled week and emits ValidationIssues
with severity tags. The orchestrator decides how to act on each issue:

    severity = 'info'           → log, keep
    severity = 'swap'           → replace one exercise from the pool
    severity = 'regen_session'  → regenerate that one session (1 LLM call)
    severity = 'fatal'          → abort, surface error

Severity philosophy: we prefer the cheapest possible fix. A duplicate
pattern is a single swap; a missing primary muscle is a regen; a
selector with zero candidates is fatal (engineering bug, not data).

Checks (in order of cost):
  1.  exercise_count_min          (≥5 per session)
  2.  total_set_budget_overrun    (>±25% of plan)
  3.  weekly_volume_above_mrv     (cap at MAV+2 per muscle)
  4.  weekly_volume_below_mev     (priority muscles only)
  5.  movement_pattern_duplicate  (same pattern twice in compound slot)
  6.  muscle_consecutive_days     (chest 2 days in a row >4 sets)
  7.  push_pull_imbalance         (weekly push:pull outside 0.7-1.4)
  8.  complexity_overrun          (any exercise > profile.complexity_cap)
  9.  equipment_mismatch          (any exercise not in profile.equipment)
  10. duration_overrun            (estimated session time > target + 25%)
"""
from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from .models import (
    AssembledSession,
    ExerciseCandidate,
    TrainingProfile,
    ValidationIssue,
    ValidationReport,
    VolumeTargets,
    WeeklyProgram,
    WeeklySplit,
)

logger = logging.getLogger(__name__)

_RULES_PATH = Path(__file__).parent / "rules" / "volume.json"
_VOLUME_RULES = json.loads(_RULES_PATH.read_text(encoding="utf-8"))
_BANDS = _VOLUME_RULES["bands"]


# ──────────────────────────────────────────────────────────────────────
#  Lookup helpers
# ──────────────────────────────────────────────────────────────────────
def _exercise_lookup_from_candidates(
    pools_by_session: dict[int, dict[str, list[ExerciseCandidate]]],
) -> dict[int, ExerciseCandidate]:
    """Flatten all pools into id-keyed lookup."""
    out: dict[int, ExerciseCandidate] = {}
    for pool in pools_by_session.values():
        for cands in pool.values():
            for c in cands:
                out[c.id] = c
    return out


def _band_mav(muscle: str, experience: str) -> int:
    bands = _BANDS.get(muscle) or _BANDS["chest"]
    return bands.get(experience, bands["intermediate"])[1]   # MAV index


def _band_mev(muscle: str, experience: str) -> int:
    bands = _BANDS.get(muscle) or _BANDS["chest"]
    return bands.get(experience, bands["intermediate"])[0]


def _muscle_of(ex: ExerciseCandidate) -> str:
    """Coarse primary muscle bucket (matches our split vocabulary)."""
    if not ex.primary_muscles:
        return "other"
    p = ex.primary_muscles[0].lower()
    # DB → internal mapping (mirrors selector but reverse)
    if p in ("lats", "middle back", "lower back", "traps"):
        return "back"
    if p == "shoulders":
        return "shoulder"
    if p == "quadriceps":
        return "quads"
    if p == "abdominals":
        return "core"
    return p


# ──────────────────────────────────────────────────────────────────────
#  Check functions (each returns 0..N ValidationIssue)
# ──────────────────────────────────────────────────────────────────────
def _check_exercise_count(session: AssembledSession) -> list[ValidationIssue]:
    if len(session.exercises) < 5:
        return [ValidationIssue(
            code="exercise_count_min",
            severity="regen_session",
            message=f"{session.session_name}: only {len(session.exercises)} exercises (min 5)",
            session_day_index=session.day_index,
        )]
    return []


def _check_set_budget(
    session: AssembledSession,
    targets: VolumeTargets,
) -> list[ValidationIssue]:
    target = next((t for t in targets.sessions if t.day_index == session.day_index), None)
    if not target:
        return []
    actual = sum(e.sets for e in session.exercises)
    budget = target.total_set_budget
    diff_pct = abs(actual - budget) / max(budget, 1) * 100
    if diff_pct > 25:
        return [ValidationIssue(
            code="total_set_budget_overrun",
            severity="info" if diff_pct <= 35 else "swap",
            message=f"{session.session_name}: {actual} sets vs budget {budget} ({diff_pct:.0f}% off)",
            session_day_index=session.day_index,
        )]
    return []


def _check_weekly_volume(
    program: WeeklyProgram,
    lookup: dict[int, ExerciseCandidate],
) -> list[ValidationIssue]:
    """Weekly set count per muscle vs MAV+2 ceiling, MEV floor for priority."""
    issues: list[ValidationIssue] = []
    per_muscle_total: Counter = Counter()
    for s in program.sessions:
        for e in s.exercises:
            ex = lookup.get(e.exercise_id)
            if not ex: continue
            muscle = _muscle_of(ex)
            per_muscle_total[muscle] += e.sets

    for muscle, total in per_muscle_total.items():
        mav = _band_mav(muscle, program.profile.experience)
        mev = _band_mev(muscle, program.profile.experience)
        ceiling = mav + 2  # safety cap above MAV
        if total > ceiling:
            issues.append(ValidationIssue(
                code="weekly_volume_above_mrv",
                severity="info",
                message=f"{muscle} weekly volume {total} > MAV+2 ({ceiling})",
            ))
        if muscle in program.profile.priority_muscles and total < mev:
            issues.append(ValidationIssue(
                code="weekly_volume_below_mev",
                severity="swap",
                message=f"priority {muscle} weekly volume {total} < MEV ({mev})",
            ))
    return issues


def _check_pattern_duplicate(
    session: AssembledSession,
    lookup: dict[int, ExerciseCandidate],
) -> list[ValidationIssue]:
    """Same movement_pattern appearing 3+ times in one session — over-narrow."""
    issues: list[ValidationIssue] = []
    pattern_count: Counter = Counter()
    for e in session.exercises:
        ex = lookup.get(e.exercise_id)
        if not ex or not ex.movement_pattern: continue
        pattern_count[ex.movement_pattern] += 1
    for pat, n in pattern_count.items():
        if n >= 3:
            issues.append(ValidationIssue(
                code="movement_pattern_duplicate",
                severity="swap",
                message=f"{session.session_name}: pattern '{pat}' used {n}x (max 2 for variety)",
                session_day_index=session.day_index,
            ))
    return issues


def _check_consecutive_days(
    program: WeeklyProgram,
    lookup: dict[int, ExerciseCandidate],
) -> list[ValidationIssue]:
    """Same muscle worked 2 consecutive days with >4 sets each → recovery hit."""
    issues: list[ValidationIssue] = []
    by_day: dict[int, Counter] = defaultdict(Counter)
    for s in program.sessions:
        for e in s.exercises:
            ex = lookup.get(e.exercise_id)
            if not ex: continue
            by_day[s.day_index][_muscle_of(ex)] += e.sets
    for d in sorted(by_day.keys()):
        next_d = d + 1
        if next_d not in by_day: continue
        for muscle, sets in by_day[d].items():
            if sets < 4: continue
            next_sets = by_day[next_d].get(muscle, 0)
            if next_sets >= 4:
                issues.append(ValidationIssue(
                    code="muscle_consecutive_days",
                    severity="info",
                    message=f"{muscle}: {sets} sets day {d}, then {next_sets} sets day {next_d} — recovery risk",
                ))
    return issues


def _check_push_pull_balance(
    program: WeeklyProgram,
    lookup: dict[int, ExerciseCandidate],
) -> list[ValidationIssue]:
    """Weekly push:pull ratio. Outside 0.7-1.4 = unbalanced."""
    push_patterns = {"horizontal_press", "vertical_press"}
    pull_patterns = {"horizontal_pull", "vertical_pull"}
    push_sets = pull_sets = 0
    for s in program.sessions:
        for e in s.exercises:
            ex = lookup.get(e.exercise_id)
            if not ex or not ex.movement_pattern: continue
            if ex.movement_pattern in push_patterns:
                push_sets += e.sets
            elif ex.movement_pattern in pull_patterns:
                pull_sets += e.sets
    if push_sets == 0 or pull_sets == 0:
        return []   # degenerate, ignore
    ratio = push_sets / pull_sets
    if ratio < 0.7 or ratio > 1.4:
        return [ValidationIssue(
            code="push_pull_imbalance",
            severity="info",
            message=f"push:pull = {push_sets}:{pull_sets} ({ratio:.2f}) outside 0.7-1.4 — postural risk",
        )]
    return []


def _check_complexity(
    session: AssembledSession,
    lookup: dict[int, ExerciseCandidate],
    profile: TrainingProfile,
) -> list[ValidationIssue]:
    """Belt-and-suspenders: selector already caps but the assembler could
    in theory pick something off-pool if our schema enum has a bug."""
    issues: list[ValidationIssue] = []
    for e in session.exercises:
        ex = lookup.get(e.exercise_id)
        if not ex or ex.complexity is None: continue
        if ex.complexity > profile.complexity_cap:
            issues.append(ValidationIssue(
                code="complexity_overrun",
                severity="swap",
                message=f"{ex.canonical_name} complexity={ex.complexity} > cap={profile.complexity_cap}",
                session_day_index=session.day_index,
                exercise_id=e.exercise_id,
            ))
    return issues


def _check_equipment(
    session: AssembledSession,
    lookup: dict[int, ExerciseCandidate],
    profile: TrainingProfile,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    allowed = set(profile.equipment)
    for e in session.exercises:
        ex = lookup.get(e.exercise_id)
        if not ex or not ex.equipment_type: continue
        if ex.equipment_type not in allowed:
            issues.append(ValidationIssue(
                code="equipment_mismatch",
                severity="swap",
                message=f"{ex.canonical_name} eq={ex.equipment_type} not in profile {sorted(allowed)}",
                session_day_index=session.day_index,
                exercise_id=e.exercise_id,
            ))
    return issues


def _check_duration(
    session: AssembledSession,
    profile: TrainingProfile,
) -> list[ValidationIssue]:
    """Rough estimate: each set = 60s work + 90s rest = 2.5min. + 5min warmup."""
    total_sets = sum(e.sets for e in session.exercises)
    estimated_min = 5 + total_sets * 2.5
    target = profile.session_duration
    if estimated_min > target * 1.25:
        return [ValidationIssue(
            code="duration_overrun",
            severity="swap",
            message=f"{session.session_name}: estimated {estimated_min:.0f}min vs target {target}min",
            session_day_index=session.day_index,
        )]
    return []


# ──────────────────────────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────────────────────────
def validate(
    program: WeeklyProgram,
    pools_by_session: dict[int, dict[str, list[ExerciseCandidate]]],
) -> ValidationReport:
    """Run all checks. Returns ValidationReport with issues + 0-100 score."""
    issues: list[ValidationIssue] = []
    lookup = _exercise_lookup_from_candidates(pools_by_session)

    for session in program.sessions:
        issues.extend(_check_exercise_count(session))
        issues.extend(_check_set_budget(session, program.targets))
        issues.extend(_check_pattern_duplicate(session, lookup))
        issues.extend(_check_complexity(session, lookup, program.profile))
        issues.extend(_check_equipment(session, lookup, program.profile))
        issues.extend(_check_duration(session, program.profile))

    issues.extend(_check_weekly_volume(program, lookup))
    issues.extend(_check_consecutive_days(program, lookup))
    issues.extend(_check_push_pull_balance(program, lookup))

    # Score: deduct per issue weighted by severity.
    weights = {"info": 1, "swap": 5, "regen_session": 15, "fatal": 50}
    deduction = sum(weights[i.severity] for i in issues)
    score = max(0, 100 - deduction)

    return ValidationReport(issues=issues, score=score)


# ──────────────────────────────────────────────────────────────────────
#  Repair — swap exercises in place (no LLM call)
# ──────────────────────────────────────────────────────────────────────
def _alternative_for(
    bad_exercise_id: int,
    pool: dict[str, list[ExerciseCandidate]],
    lookup: dict[int, ExerciseCandidate],
    already_used: set[int],
) -> Optional[ExerciseCandidate]:
    """Find an unused exercise that targets the same muscle bucket."""
    bad = lookup.get(bad_exercise_id)
    if not bad: return None
    target_muscle = _muscle_of(bad)
    candidates = pool.get(target_muscle, [])
    for c in candidates:
        if c.id != bad_exercise_id and c.id not in already_used:
            return c
    return None


def repair_swap(
    program: WeeklyProgram,
    issues: list[ValidationIssue],
    pools_by_day: dict[int, dict[str, list[ExerciseCandidate]]],
) -> tuple[WeeklyProgram, int]:
    """Apply 'swap' severity issues — replace specific exercises in-place
    using the existing candidate pool. No LLM call.

    Returns the modified program and the count of swaps applied.
    """
    lookup = _exercise_lookup_from_candidates(pools_by_day)
    used_ids: set[int] = {e.exercise_id for s in program.sessions for e in s.exercises}

    swap_issues = [i for i in issues if i.severity == "swap" and i.exercise_id]
    swaps_applied = 0
    for issue in swap_issues:
        if issue.exercise_id not in used_ids:
            continue
        day_pool = pools_by_day.get(issue.session_day_index or -1)
        if not day_pool:
            continue
        alt = _alternative_for(issue.exercise_id, day_pool, lookup, used_ids)
        if not alt:
            continue
        # mutate the program — find the session and the exercise slot
        for session in program.sessions:
            if session.day_index != issue.session_day_index:
                continue
            for ex in session.exercises:
                if ex.exercise_id == issue.exercise_id:
                    used_ids.discard(ex.exercise_id)
                    used_ids.add(alt.id)
                    ex.exercise_id = alt.id
                    swaps_applied += 1
                    break
    return program, swaps_applied
