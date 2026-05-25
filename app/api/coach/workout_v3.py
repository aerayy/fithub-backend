"""POST /coach/students/{id}/workout-programs/generate-v3

v3 workout generator endpoint. Calls the workout pipeline (Phase A-D),
persists the result, returns the program_id + validation score.

v2 endpoint (in routes.py) remains untouched — both live in parallel
during the shadow A/B phase. Flutter passes pipeline_version='v3' as a
flag to opt in.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from app.core.database import get_db
from app.core.security import require_role
from app.services.workout import pipeline
from app.services.workout.profile_analyzer import persist_profile
from app.services.workout.validator import validate
from app.services.workout.persistence import save_program

router = APIRouter(prefix="/coach", tags=["coach-workout-v3"])
logger = logging.getLogger(__name__)


@router.post("/students/{student_user_id}/workout-programs/generate-v3")
async def generate_workout_v3(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Generate a v3 workout program (rule-based pipeline)."""
    coach_id = current_user["id"]

    # Coach-student auth
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id = %s AND assigned_coach_id = %s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Bu öğrenci size atanmamış")

    try:
        program = await pipeline.orchestrate(db, student_user_id, persist=False)
    except Exception as e:
        logger.exception("v3: pipeline failed user=%s coach=%s", student_user_id, coach_id)
        raise HTTPException(status_code=502, detail=f"v3 pipeline error: {e}")

    if not program:
        raise HTTPException(status_code=502, detail="v3 pipeline returned no program")

    # Profile persist (audit)
    try:
        training_profile_id = persist_profile(db, program.profile)
    except Exception as e:
        logger.warning("v3: profile persist skipped (%s)", e)
        training_profile_id = None

    # Validation score (re-run inline; pipeline already validated but this
    # is the snapshot we persist alongside the program for review later)
    pools_by_day: dict = {}   # candidate pools aren't rehydrated post-pipeline
    score = None
    try:
        from app.services.workout.exercise_selector import select_candidates_for_session
        pools_by_day = {
            spec.day_index: select_candidates_for_session(db, spec, program.profile)
            for spec in program.split.sessions
        }
        report = validate(program, pools_by_day)
        score = report.score
        logger.info("v3: final validation score=%d issues=%d", score, len(report.issues))
    except Exception as e:
        logger.warning("v3: validation snapshot skipped (%s)", e)

    # Persist
    try:
        program_id = save_program(
            db, program,
            coach_user_id=coach_id,
            validation_score=score,
            training_profile_id=training_profile_id,
            is_active=False,   # draft — coach reviews before assigning
        )
    except Exception as e:
        logger.exception("v3: persistence failed")
        raise HTTPException(status_code=500, detail=f"persist error: {e}")

    return {
        "ok": True,
        "program_id": program_id,
        "pipeline_version": "v3",
        "validation_score": score,
        "split_id": program.split.split_id,
        "session_count": len(program.sessions),
        "training_profile_id": training_profile_id,
    }
