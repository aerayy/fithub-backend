# app/api/onboarding.py
import logging
from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extras import Json

from app.core.database import get_db
from app.schemas.onboarding import OnboardingRequest
from app.core.security import require_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/client", tags=["client"])

@router.post("/onboarding")
def save_onboarding(
    req: OnboardingRequest,
    db=Depends(get_db),
    current_user=Depends(require_role("client"))
):
    """
    Save onboarding data and update clients table.
    
    Test flow:
    1. Submit onboarding POST /client/onboarding with weight_kg, height_cm, gender, your_goal
    2. Check clients table: SELECT * FROM clients WHERE user_id = <user_id>
       - Should have onboarding_done=true, weight_kg, height_cm, gender, goal_type populated
    3. Call GET /client/daily-targets - should return 200 with computed targets
    """
    user_id = current_user["id"]
    cur = db.cursor()
    
    # Debug: Log user_id and request values
    logger.debug(f"[ONBOARDING] user_id={user_id}, weight_kg={req.weight_kg}, height_cm={req.height_cm}, gender={req.gender}, your_goal={req.your_goal}")

    # 1) Onboarding verisini kaydet / güncelle
    cur.execute(
        """
        INSERT INTO client_onboarding (
            user_id,
            full_name,
            age,
            weight_kg,
            height_cm,
            gender,
            your_goal,
            body_type,
            experience,
            how_fit,
            knee_pain,
            pushups,
            stressed,
            commit,
            pref_workout_length,
            how_motivated,
            plan_reference,
            body_part_focus,
            bad_habit,
            what_motivate,
            workout_place,
            created_at,
            updated_at
        )
        VALUES (
            %(user_id)s,
            %(full_name)s,
            %(age)s,
            %(weight_kg)s,
            %(height_cm)s,
            %(gender)s,
            %(your_goal)s,
            %(body_type)s,
            %(experience)s,
            %(how_fit)s,
            %(knee_pain)s,
            %(pushups)s,
            %(stressed)s,
            %(commit)s,
            %(pref_workout_length)s,
            %(how_motivated)s,
            %(plan_reference)s,
            %(body_part_focus)s,
            %(bad_habit)s,
            %(what_motivate)s,
            %(workout_place)s,
            NOW(),
            NOW()
        )
        ON CONFLICT (user_id) DO UPDATE SET
            full_name           = EXCLUDED.full_name,
            age                 = EXCLUDED.age,
            weight_kg           = EXCLUDED.weight_kg,
            height_cm           = EXCLUDED.height_cm,
            gender              = EXCLUDED.gender,
            your_goal           = EXCLUDED.your_goal,
            body_type           = EXCLUDED.body_type,
            experience          = EXCLUDED.experience,
            how_fit             = EXCLUDED.how_fit,
            knee_pain           = EXCLUDED.knee_pain,
            pushups             = EXCLUDED.pushups,
            stressed            = EXCLUDED.stressed,
            commit              = EXCLUDED.commit,
            pref_workout_length = EXCLUDED.pref_workout_length,
            how_motivated       = EXCLUDED.how_motivated,
            plan_reference      = EXCLUDED.plan_reference,
            body_part_focus     = EXCLUDED.body_part_focus,
            bad_habit           = EXCLUDED.bad_habit,
            what_motivate       = EXCLUDED.what_motivate,
            workout_place       = EXCLUDED.workout_place,
            updated_at          = NOW();
        """,
        {
            "user_id": current_user["id"],
            "full_name": req.full_name,
            "age": req.age,
            "weight_kg": req.weight_kg,
            "height_cm": req.height_cm,
            "gender": req.gender,
            "your_goal": req.your_goal,
            "body_type": req.body_type,
            "experience": req.experience,
            "how_fit": req.how_fit,
            "knee_pain": req.knee_pain,
            "pushups": req.pushups,
            "stressed": req.stressed,
            "commit": req.commit,
            "pref_workout_length": req.pref_workout_length,
            "how_motivated": req.how_motivated,
            "plan_reference": req.plan_reference,
            "body_part_focus": Json(req.body_part_focus) if req.body_part_focus else None,
            "bad_habit": Json(req.bad_habit) if req.bad_habit else None,
            "what_motivate": Json(req.what_motivate) if req.what_motivate else None,
            "workout_place": Json(req.workout_place) if req.workout_place else None,
        },
    )

    # 2) clients satırı yoksa oluştur (garanti)
    cur.execute(
        """
        INSERT INTO clients (user_id, onboarding_done, created_at)
        VALUES (%s, FALSE, NOW())
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )

    # 3) Validate required fields before updating clients table
    if req.weight_kg is None or req.height_cm is None:
        logger.warning(f"[ONBOARDING] Missing required measurements for user_id={user_id}: weight_kg={req.weight_kg}, height_cm={req.height_cm}")
        # Still allow onboarding to complete, but log warning
        # The daily-targets endpoint will catch this and return 400

    # 4) Update clients table with profile data and set onboarding_done = TRUE
    # Map your_goal -> goal_type for clients table
    update_params = {
        "user_id": user_id,
        "weight_kg": req.weight_kg,
        "height_cm": req.height_cm,
        "gender": req.gender,
        "goal_type": req.your_goal,  # Map your_goal to goal_type
    }
    
    logger.debug(f"[ONBOARDING] Updating clients table with params: {update_params}")
    
    cur.execute(
        """
        UPDATE clients
        SET 
            onboarding_done = TRUE,
            weight_kg = %(weight_kg)s,
            height_cm = %(height_cm)s,
            gender = %(gender)s,
            goal_type = %(goal_type)s
        WHERE user_id = %(user_id)s
        """,
        update_params,
    )
    updated_rows = cur.rowcount
    logger.debug(f"[ONBOARDING] UPDATE clients affected {updated_rows} row(s)")

    # 5) Verify the update by selecting the row
    cur.execute(
        """
        SELECT weight_kg, height_cm, gender, goal_type, onboarding_done
        FROM clients
        WHERE user_id = %s
        """,
        (user_id,),
    )
    verification_row = cur.fetchone()
    if verification_row:
        logger.debug(f"[ONBOARDING] Verification - clients row after update: {dict(verification_row)}")
    else:
        logger.error(f"[ONBOARDING] ERROR: Could not find clients row for user_id={user_id} after update!")

    db.commit()

    return {
        "success": True,
        "onboarding_done": True,
        "updated_rows": updated_rows,
    }


@router.get("/onboarding/{user_id}")
def get_onboarding(user_id: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        """
        SELECT
            id, user_id, full_name, age, gender, weight_kg, height_cm,
            your_goal, body_type, experience, how_fit, knee_pain, pushups,
            stressed, commit, pref_workout_length, how_motivated, plan_reference,
            body_part_focus, bad_habit, what_motivate, workout_place
        FROM client_onboarding
        WHERE user_id = %s
        """,
        (user_id,),
    )
    profile = cur.fetchone()
    if not profile:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    return {"profile": profile}
