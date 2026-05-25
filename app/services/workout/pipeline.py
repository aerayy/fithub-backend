"""Pipeline orchestrator — glues Stage 1-5 (Stage 6/7 land in Phase D/E).

Public entry point for the v3 workout endpoint:
    `program = await pipeline.orchestrate(conn, user_id)`

Each stage is independently testable; this module is dumb glue that
threads the Pydantic DTOs through.
"""
from __future__ import annotations

import logging
from typing import Optional

from psycopg2.extras import RealDictCursor

from .models import (
    AssembledSession,
    SessionSpec,
    SessionTargets,
    TrainingProfile,
    VolumeTargets,
    WeeklyProgram,
    WeeklySplit,
)
from .profile_analyzer import build_training_profile, persist_profile
from .split_planner import plan_split
from .volume_planner import plan_volume
from .exercise_selector import select_candidates_for_session
from .session_assembler import assemble_all_sessions, assemble_session
from .validator import validate, repair_swap

logger = logging.getLogger(__name__)


def _fetch_onboarding(conn, user_id: int) -> dict:
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT co.*
        FROM client_onboarding co
        WHERE co.user_id = %s
        ORDER BY co.id DESC LIMIT 1
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"no onboarding for user_id={user_id}")
    return dict(row)


async def orchestrate(
    conn,
    user_id: int,
    *,
    persist: bool = True,
) -> Optional[WeeklyProgram]:
    """End-to-end pipeline: onboarding → assembled week."""
    onb = _fetch_onboarding(conn, user_id)

    # Stage 1
    profile = build_training_profile(onb, user_id=user_id)
    logger.info("pipeline: profile %s/%s/%dd built", profile.experience, profile.goal, profile.days_per_week)

    # Stage 2
    split = plan_split(conn, profile)
    logger.info("pipeline: split %s (%d sessions)", split.split_id, len(split.sessions))

    # Stage 3
    targets = plan_volume(profile, split)
    logger.info(
        "pipeline: volume weekly=%s",
        {m: v for m, v in sorted(targets.weekly_per_muscle.items())},
    )

    # Stage 4: per-session candidate pools (DB-only)
    sessions_with_pool: list = []
    for spec, sess_target in zip(split.sessions, targets.sessions):
        pool = select_candidates_for_session(conn, spec, profile, pool_per_muscle=8)
        total_pool = sum(len(c) for c in pool.values())
        logger.info(
            "pipeline: pool session=%s muscles=%d total_candidates=%d",
            spec.name, len(spec.muscles), total_pool,
        )
        sessions_with_pool.append((spec, sess_target, pool))

    # Stage 5: LLM assembly (parallel sessions)
    assembled = await assemble_all_sessions(sessions_with_pool, profile)
    logger.info("pipeline: assembled %d/%d sessions", len(assembled), len(split.sessions))

    program = WeeklyProgram(
        profile=profile,
        split=split,
        targets=targets,
        sessions=assembled,
    )

    # Stage 6: Validation + repair loop
    pools_by_day: dict[int, dict] = {
        spec.day_index: pool for spec, _, pool in sessions_with_pool
    }
    report = validate(program, pools_by_day)
    logger.info(
        "pipeline: validation score=%d issues=%d (severities=%s)",
        report.score, len(report.issues),
        dict({sev: sum(1 for i in report.issues if i.severity == sev)
              for sev in ("info", "swap", "regen_session", "fatal")}),
    )

    # Repair pass — apply swaps first (cheap), then regen sessions (1 LLM each)
    if any(i.severity == "swap" for i in report.issues):
        program, n_swaps = repair_swap(program, report.issues, pools_by_day)
        logger.info("pipeline: %d swap repairs applied", n_swaps)

    regen_targets = sorted({
        i.session_day_index for i in report.issues
        if i.severity == "regen_session" and i.session_day_index is not None
    })
    if regen_targets:
        logger.info("pipeline: regen-session targets=%s", regen_targets)
        for day_idx in regen_targets:
            try:
                spec, sess_target, pool = next(
                    (s, t, p) for s, t, p in sessions_with_pool
                    if s.day_index == day_idx
                )
            except StopIteration:
                continue
            new_session = await assemble_session(spec, sess_target, pool, profile)
            if new_session:
                # replace
                program.sessions = [
                    new_session if s.day_index == day_idx else s
                    for s in program.sessions
                ]

    # Final pass — re-score after repair (won't auto-repair again, just for telemetry)
    final_report = validate(program, pools_by_day)
    logger.info(
        "pipeline: post-repair score=%d (was %d) — issues=%d",
        final_report.score, report.score, len(final_report.issues),
    )

    if persist:
        try:
            profile_id = persist_profile(conn, profile)
            logger.info("pipeline: profile persisted id=%s", profile_id)
        except Exception as e:
            logger.warning("pipeline: profile persist skipped (%s)", e)

    return program
