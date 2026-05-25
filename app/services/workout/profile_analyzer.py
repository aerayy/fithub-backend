"""Stage 1 — ProfileAnalyzer.

Deterministic normalization of a raw client_onboarding row into a
TrainingProfile. No LLM, no DB writes (caller persists).

Why deterministic:
- Same onboarding row always yields the same profile (testable).
- Removes "AI interprets the user differently each call" instability
  that v2's monolithic prompt suffered from.

The output TrainingProfile is the input to all downstream pipeline
stages (SplitPlanner, VolumePlanner, ExerciseSelector).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from .models import (
    Experience,
    Gender,
    Goal,
    EquipmentType,
    TrainingProfile,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
#  Vocabulary mappings — Turkish onboarding values → English canonical
# ──────────────────────────────────────────────────────────────────────
_GOAL_MAP: dict[str, Goal] = {
    # Hypertrophy
    "kas kazanmak": "hypertrophy",
    "kas yapmak": "hypertrophy",
    "muscle gain": "hypertrophy",
    "gain muscle": "hypertrophy",
    "kas kazanma": "hypertrophy",
    # Strength
    "güçlenmek": "strength",
    "guclenmek": "strength",
    "strength": "strength",
    "get stronger": "strength",
    # Fat loss
    "yağ yakmak": "fat_loss",
    "yag yakmak": "fat_loss",
    "kilo vermek": "fat_loss",
    "weight loss": "fat_loss",
    "lose weight": "fat_loss",
    # Recomp
    "fit kalmak": "general",
    "general fitness": "general",
    "sağlıklı": "general",
    "saglikli": "general",
    "şıkılaşmak": "recomp",
    "sikilasmak": "recomp",
    "tone": "recomp",
    "recomp": "recomp",
    # Endurance
    "dayanıklılık": "endurance",
    "endurance": "endurance",
}

# Experience bucketing — combines self-reported experience + how_fit + pushup
# capability for a more robust signal than relying on one field.
_EXPERIENCE_LITERAL: dict[str, Experience] = {
    "beginner": "beginner",
    "yeni başlıyorum": "beginner",
    "yeni basliyorum": "beginner",
    "hic": "beginner",
    "1 yıldan az": "beginner",
    "<1 year": "beginner",
    "intermediate": "intermediate",
    "orta seviye": "intermediate",
    "1-3 yıl": "intermediate",
    "1-3 years": "intermediate",
    "advanced": "advanced",
    "ileri seviye": "advanced",
    "3+ yıl": "advanced",
    "3+ years": "advanced",
}

_FITNESS_LIT: dict[str, int] = {
    # how_fit → 0-3 contribution to experience
    "not fit": 0,
    "az hareketli": 0,
    "average": 1,
    "orta": 1,
    "fit": 2,
    "good": 2,
    "very fit": 3,
    "athlete": 3,
}

_PUSHUP_LIT: dict[str, int] = {
    # pushups → 0-2 contribution
    "0-5": 0, "0": 0, "few": 0,
    "5-10": 1,
    "10-20": 1,
    "20+": 2, "20-30": 2, "30+": 2,
}

# Equipment: workout_place value → list of equipment_type tokens
_PLACE_EQUIPMENT: dict[str, list[EquipmentType]] = {
    "ev": ["bodyweight", "dumbbell", "band"],
    "home": ["bodyweight", "dumbbell", "band"],
    "evde": ["bodyweight", "dumbbell", "band"],
    "spor salonu": ["barbell", "dumbbell", "cable", "machine", "bodyweight", "smith"],
    "gym": ["barbell", "dumbbell", "cable", "machine", "bodyweight", "smith"],
    "salon": ["barbell", "dumbbell", "cable", "machine", "bodyweight", "smith"],
    "açık alan": ["bodyweight", "kettlebell"],
    "outdoor": ["bodyweight", "kettlebell"],
}

# session_duration buckets — pref_workout_length value → minutes
_DURATION_MIN: dict[str, int] = {
    "short": 30,
    "kısa": 30,
    "kisa": 30,
    "medium": 45,
    "orta": 45,
    "long": 60,
    "uzun": 60,
    "very long": 75,
    "60+": 60,
    "45 dk": 45,
    "60 dk": 60,
    "75 dk": 75,
}

# Body-focus token → priority muscle (TrainingProfile.priority_muscles)
_FOCUS_MAP: dict[str, str] = {
    "chest": "chest",
    "göğüs": "chest",
    "gogus": "chest",
    "back": "back",
    "sırt": "back",
    "sirt": "back",
    "shoulders": "shoulder",
    "omuz": "shoulder",
    "arms": "biceps",   # ambiguous, pick biceps as proxy; user can refine
    "kol": "biceps",
    "biceps": "biceps",
    "triceps": "triceps",
    "legs": "quads",
    "bacak": "quads",
    "quads": "quads",
    "hamstrings": "hamstrings",
    "glutes": "glutes",
    "kalça": "glutes",
    "kalca": "glutes",
    "core": "core",
    "karın": "core",
    "karin": "core",
    "abs": "core",
    "calves": "calves",
    "baldır": "calves",
    "baldir": "calves",
}

# health_problems token → contraindication
_HEALTH_CONTRA: dict[str, str] = {
    "diz": "knee_pain",
    "knee": "knee_pain",
    "bel": "lower_back",
    "lower_back": "lower_back",
    "lower back": "lower_back",
    "omuz": "shoulder_impingement",
    "shoulder": "shoulder_impingement",
    "kalp": "cardio_caution",
    "heart": "cardio_caution",
    "tansiyon": "cardio_caution",
    "blood pressure": "cardio_caution",
}


# ──────────────────────────────────────────────────────────────────────
#  Internal normalizers
# ──────────────────────────────────────────────────────────────────────
def _norm(s: Any) -> str:
    if s is None:
        return ""
    return str(s).strip().lower()


def _coerce_jsonb_list(v: Any) -> list:
    """client_onboarding columns are JSONB lists or already-decoded lists."""
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            j = json.loads(v)
            return j if isinstance(j, list) else []
        except Exception:
            return []
    return []


def _norm_goal(v: Any) -> Goal:
    s = _norm(v)
    return _GOAL_MAP.get(s, "general")


def _bucket_experience(exp_field: Any, how_fit: Any, pushup: Any) -> Experience:
    """Combine 3 signals for a robust experience bucket."""
    direct = _EXPERIENCE_LITERAL.get(_norm(exp_field))
    if direct:
        return direct
    # Composite score (0-7 range)
    score = 0
    score += _FITNESS_LIT.get(_norm(how_fit), 1)
    score += _PUSHUP_LIT.get(_norm(pushup), 1)
    if score <= 1:
        return "beginner"
    if score <= 3:
        return "intermediate"
    return "advanced"


def _coerce_days(raw: Any) -> int:
    """preferred_workout_days can be: list of day names, list of indices,
    int, str. Returns count 1-7."""
    days = _coerce_jsonb_list(raw)
    if days:
        n = len(set(days))
        return max(1, min(7, n))
    # fallback
    if isinstance(raw, int):
        return max(1, min(7, raw))
    return 3


def _bucket_duration(raw: Any) -> int:
    s = _norm(raw)
    if s in _DURATION_MIN:
        return _DURATION_MIN[s]
    # try to parse "45", "60dk" etc.
    for tok in s.split():
        try:
            n = int("".join(c for c in tok if c.isdigit()))
            if 20 <= n <= 180:
                return n
        except Exception:
            continue
    return 45


def _equipment_from_place(workout_place: Any) -> list[EquipmentType]:
    places = _coerce_jsonb_list(workout_place)
    if not places and isinstance(workout_place, str):
        places = [workout_place]
    out: set[EquipmentType] = set()
    for p in places:
        ts = _PLACE_EQUIPMENT.get(_norm(p), [])
        for t in ts:
            out.add(t)
    if not out:
        out = {"bodyweight"}
    return sorted(out)


def _priority_muscles(
    body_focus_raw: Any,
    gender: Gender,
    goal: Goal,
    explicit_count: int = 0,
) -> list[str]:
    """body_focus values from onboarding, normalized. Soft female-glute
    recommendation only if (a) gender=female, (b) goal=hypertrophy,
    (c) no body_focus explicitly selected — and is just a SUGGESTION
    that callers can override."""
    raw = _coerce_jsonb_list(body_focus_raw)
    out: list[str] = []
    for r in raw:
        muscle = _FOCUS_MAP.get(_norm(r))
        if muscle and muscle not in out:
            out.append(muscle)

    if not out and gender == "female" and goal == "hypertrophy":
        # SOFT recommendation, not hard injection
        out = ["glutes"]
        logger.info("profile_analyzer: soft glute-priority for female hypertrophy user")

    return out


def _contraindications(knee_pain: Any, health_problems: Any) -> list[str]:
    out: set[str] = set()
    if _norm(knee_pain) in {"var", "evet", "yes", "true"}:
        out.add("knee_pain")
    health = _coerce_jsonb_list(health_problems) if isinstance(health_problems, str) else (
        health_problems or []
    )
    for h in health:
        key = _HEALTH_CONTRA.get(_norm(h))
        if key:
            out.add(key)
    return sorted(out)


def _complexity_cap(experience: Experience) -> int:
    """Beginners can't access Olympic / pistol squat — see DB classify."""
    return {"beginner": 2, "intermediate": 4, "advanced": 5}[experience]


def _norm_gender(v: Any) -> Gender:
    s = _norm(v)
    if s in {"male", "erkek", "m", "bay"}:
        return "male"
    if s in {"female", "kadin", "kadın", "f", "bayan"}:
        return "female"
    if s in {"other", "diger", "diğer", "nonbinary"}:
        return "other"
    return "unspecified"


# ──────────────────────────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────────────────────────
def build_training_profile(onboarding_row: dict, user_id: int) -> TrainingProfile:
    """Translate a raw client_onboarding row into a TrainingProfile.

    Args:
        onboarding_row: dict from `SELECT * FROM client_onboarding WHERE user_id=X`
        user_id: explicit user_id (onboarding row may not always carry it cleanly)
    """
    goal = _norm_goal(onboarding_row.get("your_goal"))
    experience = _bucket_experience(
        onboarding_row.get("experience"),
        onboarding_row.get("how_fit"),
        onboarding_row.get("pushups"),
    )
    days = _coerce_days(onboarding_row.get("preferred_workout_days"))
    duration = _bucket_duration(onboarding_row.get("pref_workout_length"))
    equipment = _equipment_from_place(onboarding_row.get("workout_place"))
    gender = _norm_gender(onboarding_row.get("gender"))
    priority = _priority_muscles(onboarding_row.get("body_part_focus"), gender, goal)
    contras = _contraindications(
        onboarding_row.get("knee_pain"),
        onboarding_row.get("health_problems"),
    )

    return TrainingProfile(
        user_id=user_id,
        goal=goal,
        experience=experience,
        days_per_week=days,
        session_duration=duration,
        equipment=equipment,
        priority_muscles=priority,
        contraindications=contras,
        gender=gender,
        complexity_cap=_complexity_cap(experience),
        source_onboarding_id=onboarding_row.get("id"),
        recommended_split=None,  # split planner fills this
    )


def persist_profile(conn, profile: TrainingProfile) -> int:
    """Insert into training_profiles, return new id."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO training_profiles
            (user_id, goal, experience, days_per_week, session_duration,
             equipment, priority_muscles, contraindications, gender,
             complexity_cap, source_onboarding_id, recommended_split)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            profile.user_id,
            profile.goal,
            profile.experience,
            profile.days_per_week,
            profile.session_duration,
            profile.equipment,
            profile.priority_muscles,
            profile.contraindications,
            profile.gender if profile.gender != "unspecified" else None,
            profile.complexity_cap,
            profile.source_onboarding_id,
            profile.recommended_split,
        ),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    return new_id
