"""Stage 5 — SessionAssembler.

THE ONLY LLM CALL IN THE PIPELINE.

Input is heavily preprocessed:
  • SessionSpec (which muscles)
  • SessionTargets (set budget per muscle, exercise_count_hint)
  • Pre-filtered candidate pool (ExerciseSelector did the SQL work)

Output is structurally constrained:
  • exercise_id enum = ONLY the pool's ids (physically can't hallucinate)
  • sets bounded 2-6, reps from a fixed pattern enum, rir 0-5
  • array minItems/maxItems = exercise_count_hint ± 1

This is what we mean by "narrow LLM": the model's freedom is order,
loading pattern, and choosing which of the pre-validated options fit
best given the per-muscle budget. It cannot invent, miscount, or
violate equipment/complexity rules.

Token budget: ~2k input, ~500 output → ~$0.003 / session at gpt-4.1-mini.
A 5-session week ≈ $0.015. Far cheaper than v2's monolithic call.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import OPENAI_API_KEY

# Model knob — env var lets us A/B without code change.
# Default gpt-4.1 (5x mini cost but 1.5-2x faster + better instruction following).
# Each session costs ~$0.012 → 5-session week ~$0.06, well within Pro tier margin.
_WORKOUT_MODEL = os.getenv("WORKOUT_LLM_MODEL", "gpt-4.1")
from .models import (
    AssembledExercise,
    AssembledSession,
    ExerciseCandidate,
    SessionSpec,
    SessionTargets,
    TrainingProfile,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
#  Schema vocab
# ──────────────────────────────────────────────────────────────────────
REP_PATTERN_ENUM = [
    "5", "6", "8", "10", "12", "15", "20",
    "5-8", "6-8", "8-10", "8-12", "10-12", "10-15", "12-15", "15-20",
    "20-25", "Hata Noktası", "Maksimum",
    "30 saniye", "45 saniye", "60 saniye",
]


def _build_schema(candidate_ids: list[int], min_count: int, max_count: int) -> dict:
    """Strict JSON schema — id enum + bounded counts + clamped sets/reps/RIR.

    `min_count` / `max_count` enforce session length so the assembler
    can't return a thin program."""
    return {
        "type": "object",
        "properties": {
            "exercises": {
                "type": "array",
                "minItems": min_count,
                "maxItems": max_count,
                "items": {
                    "type": "object",
                    "properties": {
                        "exercise_id": {"type": "integer", "enum": candidate_ids},
                        "sets": {"type": "integer", "minimum": 2, "maximum": 6},
                        "reps": {"type": "string", "enum": REP_PATTERN_ENUM},
                        "rir": {"type": "integer", "minimum": 0, "maximum": 5},
                        "rationale": {"type": "string", "maxLength": 80},
                    },
                    "required": ["exercise_id", "sets", "reps", "rir", "rationale"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["exercises"],
        "additionalProperties": False,
    }


# ──────────────────────────────────────────────────────────────────────
#  Prompt
# ──────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = (
    "Sen IFBB Pro standartlarında 20+ yıl deneyimli profesyonel fitness "
    "koçusun. Görevin: VERİLEN HAVUZDAN egzersiz seçip, sırala ve "
    "set/tekrar/RIR ata. Egzersiz uydurma; sadece havuzdaki id'leri "
    "kullanabilirsin. Sıralama profesyonel pattern: COMPOUND → MID → "
    "ISOLATION (ağırdan hafife). Sadece JSON döndür."
)


def _format_candidates_for_prompt(
    pool: dict[str, list[ExerciseCandidate]],
) -> str:
    """Compact tabular pool the LLM can scan."""
    lines = []
    for muscle, cands in pool.items():
        lines.append(f"\n### {muscle.upper()} havuzu ({len(cands)} egzersiz):")
        for c in cands:
            tags = []
            if c.movement_pattern: tags.append(f"pat={c.movement_pattern}")
            if c.equipment_type: tags.append(f"eq={c.equipment_type}")
            if c.complexity is not None: tags.append(f"cx={c.complexity}")
            if c.fatigue_score is not None: tags.append(f"fat={c.fatigue_score}")
            if c.stability_requirement is not None: tags.append(f"sr={c.stability_requirement}")
            tagstr = " ".join(tags)
            lines.append(f"  - id={c.id} \"{c.canonical_name}\" [{tagstr}]")
    return "\n".join(lines)


def _format_targets_for_prompt(targets: SessionTargets) -> str:
    by_muscle = ", ".join(f"{m.muscle}={m.sets}" for m in targets.per_muscle_sets)
    return (
        f"Bu seans için hedef set dağılımı: {by_muscle}\n"
        f"Toplam set budget: {targets.total_set_budget}\n"
        f"Hedef egzersiz sayısı: ~{targets.exercise_count_hint}"
    )


def _build_user_prompt(
    session: SessionSpec,
    targets: SessionTargets,
    pool: dict[str, list[ExerciseCandidate]],
    profile: TrainingProfile,
) -> str:
    return f"""SEANS: {session.name}
Kas grupları: {", ".join(session.muscles)}
Profil: {profile.experience} seviyesi, hedef={profile.goal}, süre≈{profile.session_duration}dk
Karşı-endikasyonlar: {", ".join(profile.contraindications) or "yok"}

{_format_targets_for_prompt(targets)}

EGZERSİZ HAVUZU (sadece bu id'lerden seç):
{_format_candidates_for_prompt(pool)}

KURALLAR:
1. exercise_count_hint'e yakın say (±1 OK). MUTLAK MİNİMUM 5 egzersiz.
2. Her muscle için hedef set sayısına yaklaş — total budget aşma.
3. SIRALAMA: 1-2 compound (fatigue_score yüksek + complexity ≥2) ÖNCE,
   sonra mid varyasyonlar, en sonda isolation (fatigue düşük).
4. Aynı kası 3'ten fazla egzersizle döküme — varyasyon önemli.
5. sets: ağır compound 4-5, hipertrofi 3-4, isolation 3.
   reps: compound 6-8 ya da 8-10, mid 8-12, isolation 10-15.
   RIR: compound 1-2, isolation 0-1 (failure'a yakın).
6. rationale alanı kısa (≤80 karakter): neden bu hareketi/parametreyi seçtin."""


# ──────────────────────────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────────────────────────
async def assemble_session(
    session: SessionSpec,
    targets: SessionTargets,
    pool: dict[str, list[ExerciseCandidate]],
    profile: TrainingProfile,
    *,
    timeout_s: float = 60.0,
) -> Optional[AssembledSession]:
    """Single LLM call → ordered exercises for the session.

    Returns None on hard failure (caller can retry or skip).
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")

    # Gather all candidate ids — schema enum
    all_ids: list[int] = []
    seen: set[int] = set()
    for cands in pool.values():
        for c in cands:
            if c.id not in seen:
                seen.add(c.id)
                all_ids.append(c.id)

    if len(all_ids) < 5:
        logger.error(
            "assembler: pool too small (%d) for session=%s",
            len(all_ids), session.name,
        )
        return None

    target_count = targets.exercise_count_hint
    min_count = max(5, target_count - 1)
    max_count = min(8, target_count + 1)
    if min_count > max_count:
        min_count, max_count = 5, 8

    schema = _build_schema(all_ids, min_count, max_count)
    user_prompt = _build_user_prompt(session, targets, pool, profile)

    client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=timeout_s, max_retries=1)

    async def _do_call():
        return await client.chat.completions.create(
            model=_WORKOUT_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "session_assembly",
                    "schema": schema,
                    "strict": True,
                },
            },
            temperature=0.3,
            max_tokens=1500,
        )

    t0 = time.monotonic()
    try:
        response = await asyncio.wait_for(_do_call(), timeout=timeout_s)
    except asyncio.TimeoutError:
        logger.error("assembler: timeout session=%s after %.1fs", session.name, timeout_s)
        return None
    dur = time.monotonic() - t0

    if not response.choices:
        return None
    raw = response.choices[0].message.content or ""
    finish = response.choices[0].finish_reason
    logger.info(
        "assembler: session=%s done in %.1fs finish=%s usage=%s",
        session.name, dur, finish, getattr(response, "usage", None),
    )
    if finish == "length":
        logger.error("assembler: response truncated (max_tokens)")
        return None

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        logger.exception("assembler: invalid JSON")
        return None

    exercises_raw = payload.get("exercises") or []
    exercises = [
        AssembledExercise(
            exercise_id=int(e["exercise_id"]),
            sets=int(e["sets"]),
            reps=str(e["reps"]),
            rir=int(e["rir"]),
            rationale=str(e.get("rationale", ""))[:80],
        )
        for e in exercises_raw
    ]

    return AssembledSession(
        session_name=session.name,
        day_index=session.day_index,
        exercises=exercises,
    )


async def assemble_all_sessions(
    sessions: list[tuple[SessionSpec, SessionTargets, dict[str, list[ExerciseCandidate]]]],
    profile: TrainingProfile,
) -> list[AssembledSession]:
    """Parallel asyncio.gather of per-session assembles. Each session is
    independent — concurrency = number of sessions."""
    tasks = [
        assemble_session(spec, tgt, pool, profile)
        for spec, tgt, pool in sessions
    ]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return [r for r in results if r is not None]
