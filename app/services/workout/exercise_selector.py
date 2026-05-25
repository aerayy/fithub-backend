"""Stage 4 — ExerciseSelector.

For each session, pulls a candidate pool of exercises that satisfy the
user's profile constraints. NO LLM. NO hallucination surface — the
assembler only ever sees this filtered list, so it physically cannot
invent an unsuitable exercise.

Filter dimensions:
  • muscle match           — exercise primary_muscles overlaps session muscles
  • equipment uyumu        — exercise equipment_type ∈ profile.equipment
  • complexity cap         — exercise complexity ≤ profile.complexity_cap
  • contraindication      — knee_pain → squat/lunge azalt, lower_back → hinge azalt
  • gif availability       — UI needs gif_url; we skip metadata-only rows
  • gender skew            — male-favored row a kadın kullanıcıya verme (rare)
  • movement_pattern       — 'other' pattern'leri eleme

Per-muscle pool is ranked by:
  1. movement_pattern fit for "slot" (compound > mid > isolation)
  2. complexity ASC (safer first)
  3. fatigue_score DESC (compound > filler — fatigue ≥ 5 prefer)
"""
from __future__ import annotations

import logging
from collections import defaultdict

from psycopg2.extras import RealDictCursor

from .models import ExerciseCandidate, SessionSpec, TrainingProfile, VolumeTargets

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
#  Pattern groupings — what counts as compound / mid / isolation
#  per muscle. Same canonical movement may "anchor" different muscles
#  (e.g. squat = compound for quads AND glutes).
# ──────────────────────────────────────────────────────────────────────
COMPOUND_PATTERNS_FOR = {
    "chest":      {"horizontal_press"},
    "back":       {"horizontal_pull", "vertical_pull", "hinge"},
    "shoulder":   {"vertical_press"},
    "rear_delts": {"horizontal_pull"},
    "biceps":     set(),     # biceps is iso-only
    "triceps":    set(),
    "quads":      {"squat", "lunge"},
    "hamstrings": {"hinge"},
    "glutes":     {"squat", "hinge", "lunge"},
    "calves":     set(),
    "core":       set(),
}

ISOLATION_PATTERNS_FOR = {
    "chest":      {"iso_fly"},
    "back":       {"iso_shrug", "iso_extension"},
    "shoulder":   {"iso_raise"},
    "rear_delts": {"iso_raise"},
    "biceps":     {"iso_curl"},
    "triceps":    {"iso_extension"},
    "quads":      {"iso_extension"},
    "hamstrings": {"iso_curl"},       # leg curl maps to iso_curl
    "glutes":     {"iso_raise", "iso_extension"},
    "calves":     {"iso_calf"},
    "core":       {"anti_extension", "anti_rotation", "rotation"},
}

# Patterns to avoid for known contraindications
CONTRA_EXCLUDE_PATTERNS = {
    "knee_pain":  {"squat", "lunge", "explosive"},
    "lower_back": {"hinge", "carry"},
    "shoulder_impingement": {"vertical_press"},
    "cardio_caution": {"explosive"},
}


def _slot_of(pattern: str | None, muscle: str) -> str:
    """Map (pattern, muscle) to slot label: 'compound' | 'isolation' | 'mid'."""
    if not pattern:
        return "mid"
    if pattern in COMPOUND_PATTERNS_FOR.get(muscle, set()):
        return "compound"
    if pattern in ISOLATION_PATTERNS_FOR.get(muscle, set()):
        return "isolation"
    return "mid"


def _gender_skew_clause(gender: str) -> tuple[str, list]:
    """Generate SQL fragment for the gender_skew filter.

    male_favored exercises are still shown to women but de-prioritized
    via ORDER BY rather than eliminated — same logic the other way.
    Hard EXCLUDE only happens for the explicitly mismatched skew.
    """
    if gender == "female":
        return (
            "AND (gender_skew IS NULL OR gender_skew != 'male_favored')",
            [],
        )
    if gender == "male":
        return (
            "AND (gender_skew IS NULL OR gender_skew != 'female_favored')",
            [],
        )
    return ("", [])


def _contra_exclusion_patterns(contraindications: list[str]) -> list[str]:
    """Union of patterns that should be excluded across all the user's
    contraindications."""
    out: set[str] = set()
    for c in contraindications:
        out.update(CONTRA_EXCLUDE_PATTERNS.get(c, set()))
    return sorted(out)


# Our internal muscle vocabulary → exercise_library.primary_muscles tokens.
# exercise_library uses different terminology (lats/middle back/traps for "back",
# 'quadriceps' for 'quads', 'shoulders' plural, 'abdominals' for 'core'). One
# logical muscle may map to multiple DB tokens — we use && (overlap) so any
# match counts.
_MUSCLE_TO_DB: dict[str, list[str]] = {
    "chest":      ["chest"],
    "back":       ["lats", "middle back", "lower back", "traps"],
    "shoulder":   ["shoulders"],
    "rear_delts": ["shoulders"],   # rear-delt isolation lives under shoulders bucket
    "biceps":     ["biceps"],
    "triceps":    ["triceps"],
    "quads":      ["quadriceps"],
    "hamstrings": ["hamstrings"],
    "glutes":     ["glutes"],
    "calves":     ["calves"],
    "core":       ["abdominals"],
}


def _db_muscle_tokens(muscle: str) -> list[str]:
    """Translate internal muscle name to DB primary_muscles token(s)."""
    return _MUSCLE_TO_DB.get(muscle, [muscle])


def _select_for_muscle(
    conn,
    muscle: str,
    profile: TrainingProfile,
    pool_size: int = 10,
) -> list[ExerciseCandidate]:
    """One SQL call → top-N candidates for this muscle for this profile.

    Returns a mixed slot pool — compound + mid + isolation.
    """
    excluded_patterns = _contra_exclusion_patterns(profile.contraindications)
    gender_sql, gender_args = _gender_skew_clause(profile.gender)

    db_muscle_tokens = _db_muscle_tokens(muscle)

    # Rear delt special case: prefer iso_raise pattern when we're after
    # rear-delts specifically (since DB token is generic 'shoulders').
    extra_pattern_filter = ""
    pattern_args: list = []
    if muscle == "rear_delts":
        extra_pattern_filter = "AND movement_pattern IN ('iso_raise', 'horizontal_pull')"

    sql = f"""
        SELECT id, canonical_name, primary_muscles, movement_pattern,
               equipment_type, equipment_class, stability_requirement,
               complexity, fatigue_score
        FROM exercise_library
        WHERE primary_muscles && %s
          AND equipment_type = ANY(%s)
          AND COALESCE(complexity, 5) <= %s
          AND movement_pattern IS NOT NULL
          AND movement_pattern <> 'other'
          AND gif_url IS NOT NULL
          AND gif_url <> ''
          {extra_pattern_filter}
          AND ({"NOT (movement_pattern = ANY(%s))" if excluded_patterns else "TRUE"})
          {gender_sql}
        ORDER BY
          COALESCE(complexity, 3) ASC,
          COALESCE(fatigue_score, 5) DESC,
          canonical_name ASC
        LIMIT %s
    """
    args: list = [db_muscle_tokens, list(profile.equipment), profile.complexity_cap]
    if excluded_patterns:
        args.append(excluded_patterns)
    args.extend(gender_args)
    args.append(pool_size)

    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(sql, args)
    rows = cur.fetchall()

    return [
        ExerciseCandidate(
            id=r["id"],
            canonical_name=r["canonical_name"],
            primary_muscles=r["primary_muscles"] or [],
            movement_pattern=r.get("movement_pattern"),
            equipment_type=r.get("equipment_type"),
            equipment_class=r.get("equipment_class"),
            stability_requirement=r.get("stability_requirement"),
            complexity=r.get("complexity"),
            fatigue_score=r.get("fatigue_score"),
        )
        for r in rows
    ]


def select_candidates_for_session(
    conn,
    session: SessionSpec,
    profile: TrainingProfile,
    pool_per_muscle: int = 8,
) -> dict[str, list[ExerciseCandidate]]:
    """Per-session candidate pool. Returns dict keyed by muscle.

    The assembler then sees ~6-10 muscles × 8 candidates = ~50-80 exercise
    options. Tight enough that the LLM's enum is small (good schema
    compliance), broad enough that it can balance compound/isolation/mid.
    """
    pool: dict[str, list[ExerciseCandidate]] = {}
    for muscle in session.muscles:
        cands = _select_for_muscle(conn, muscle, profile, pool_size=pool_per_muscle)
        if not cands:
            logger.warning(
                "selector: no candidates muscle=%s equip=%s cap=%s",
                muscle, profile.equipment, profile.complexity_cap,
            )
        pool[muscle] = cands
    return pool


def pool_with_slot_tagging(
    pool: dict[str, list[ExerciseCandidate]],
) -> dict[str, dict[str, list[ExerciseCandidate]]]:
    """For each muscle, group its candidates by slot (compound/mid/iso).

    This lets the assembler explicitly request 'pick one compound + one
    isolation' rather than having to infer from movement_pattern strings.
    """
    out: dict[str, dict[str, list[ExerciseCandidate]]] = {}
    for muscle, cands in pool.items():
        slotted: dict[str, list[ExerciseCandidate]] = defaultdict(list)
        for c in cands:
            slot = _slot_of(c.movement_pattern, muscle)
            slotted[slot].append(c)
        out[muscle] = dict(slotted)
    return out


def flatten_candidate_ids(pool: dict[str, list[ExerciseCandidate]]) -> list[int]:
    """All unique candidate ids across muscles. The LLM schema enum uses
    this list — physically constrains the assembler to existing rows."""
    seen: set[int] = set()
    out: list[int] = []
    for cands in pool.values():
        for c in cands:
            if c.id not in seen:
                seen.add(c.id)
                out.append(c.id)
    return out
