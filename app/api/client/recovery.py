import json
import logging
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from psycopg2.extras import RealDictCursor, Json

from app.core.database import get_db
from app.core.security import require_role
from app.core.config import OPENAI_API_KEY
from .routes import router

logger = logging.getLogger(__name__)


@router.get("/recovery-tips")
def get_recovery_tips(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    user_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Check cache (valid for today)
    cur.execute(
        """
        SELECT tips_json, generated_at
        FROM client_recovery_cache
        WHERE user_id = %s AND generated_at::date = CURRENT_DATE
        """,
        (user_id,),
    )
    cached = cur.fetchone()
    if cached:
        return cached["tips_json"]

    # Fetch client onboarding data
    cur.execute(
        """
        SELECT
            co.age, co.weight_kg, co.height_cm, co.gender, co.your_goal,
            co.experience, co.how_fit, co.knee_pain, co.stressed,
            co.body_part_focus, co.pref_workout_length, co.workout_place,
            co.bad_habit, co.full_name, u.email
        FROM client_onboarding co
        JOIN users u ON u.id = co.user_id
        WHERE co.user_id = %s
        """,
        (user_id,),
    )
    client_data = cur.fetchone()

    if not client_data:
        raise HTTPException(status_code=404, detail="Client onboarding data not found")

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        from openai import OpenAI
    except ImportError:
        raise HTTPException(status_code=500, detail="OpenAI library not installed")

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        age = client_data.get("age") or "unknown"
        weight = client_data.get("weight_kg") or "unknown"
        height = client_data.get("height_cm") or "unknown"
        gender = client_data.get("gender") or "unknown"
        goal = client_data.get("your_goal") or "general fitness"
        experience = client_data.get("experience") or "beginner"
        fitness_level = client_data.get("how_fit") or "beginner"
        knee_pain = client_data.get("knee_pain")
        stress = client_data.get("stressed") or "unknown"
        workout_place = client_data.get("workout_place") or "gym"
        body_focus = client_data.get("body_part_focus")
        bad_habits = client_data.get("bad_habit")
        workout_length = client_data.get("pref_workout_length") or "45-60 minutes"

        injury_note = ""
        if knee_pain:
            injury_note = " The client has knee pain — recommend low-impact recovery exercises and avoid deep stretches on the knees."

        body_focus_desc = ""
        if body_focus:
            if isinstance(body_focus, dict):
                body_focus_desc = f" Focus areas: {', '.join(str(v) for v in body_focus.values())}."
            elif isinstance(body_focus, list):
                body_focus_desc = f" Focus areas: {', '.join(str(v) for v in body_focus)}."

        habits_desc = ""
        if bad_habits:
            if isinstance(bad_habits, list):
                habits_desc = f" Bad habits to address: {', '.join(str(h) for h in bad_habits)}."
            elif isinstance(bad_habits, dict):
                habits_desc = f" Bad habits to address: {', '.join(str(v) for v in bad_habits.values())}."

        prompt = f"""Generate personalized recovery tips for a {age}-year-old {gender} fitness client.

Client Profile:
- Weight: {weight} kg, Height: {height} cm
- Fitness goal: {goal}
- Experience: {experience}, Fitness level: {fitness_level}
- Stress level: {stress}
- Preferred workout length: {workout_length}
- Workout place: {workout_place}
{injury_note}{body_focus_desc}{habits_desc}

Generate 5-6 personalized recovery tips in JSON format. Return ONLY valid JSON (no markdown) with this structure:
{{
  "tips": [
    {{
      "category": "sleep|nutrition|mobility|hydration|stress|stretching",
      "icon": "bed|restaurant|fitness_center|water_drop|self_improvement|accessibility_new",
      "title": "Short title (max 4 words)",
      "description": "Detailed explanation why this is important for this specific client (2-3 sentences)",
      "action": "One specific actionable step to do today"
    }}
  ],
  "summary": "One sentence personalized summary of the recovery plan"
}}

Rules:
- Tips must be personalized based on the client's profile, goals, and constraints
- If client has knee pain, include a mobility tip specifically for knee recovery
- If stress level is high, include a stress management tip
- Always include sleep, nutrition, and hydration tips
- Use encouraging, professional tone
- Actions should be specific and doable today
- Write in Turkish language"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert sports recovery specialist. Generate personalized, evidence-based recovery tips in JSON format only. Always respond in Turkish.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        result = json.loads(response.choices[0].message.content)

        # Validate structure
        if "tips" not in result or not isinstance(result["tips"], list):
            raise ValueError("Invalid response structure")

        # Cache the result
        cur.execute(
            """
            INSERT INTO client_recovery_cache (user_id, tips_json, generated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET tips_json = EXCLUDED.tips_json, generated_at = NOW()
            """,
            (user_id, Json(result)),
        )
        db.commit()

        logger.info(f"Recovery tips generated for user_id={user_id}, tip_count={len(result['tips'])}")
        return result

    except json.JSONDecodeError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Invalid AI response: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating recovery tips for user_id={user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating recovery tips: {str(e)}")
