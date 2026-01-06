# app/api/onboarding.py
from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extras import Json

from app.core.database import get_db
from app.schemas.onboarding import OnboardingRequest
from app.core.security import require_role

router = APIRouter(prefix="/client", tags=["client"])

@router.post("/onboarding")
def save_onboarding(req: OnboardingRequest, db=Depends(get_db), current_user=Depends(require_role("client"))):
    cur = db.cursor()

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
            updated_at          = NOW()
        RETURNING id, user_id, full_name, age, weight_kg, height_cm, your_goal, experience,
                  body_part_focus, bad_habit, what_motivate, workout_place;
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
            "body_part_focus": Json(req.body_part_focus) if req.body_part_focus is not None else None,
            "bad_habit": Json(req.bad_habit) if req.bad_habit is not None else None,
            "what_motivate": Json(req.what_motivate) if req.what_motivate is not None else None,
            "workout_place": Json(req.workout_place) if req.workout_place is not None else None,
        },
    )

    profile = cur.fetchone()
    db.commit()
    return {"profile": profile}

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
