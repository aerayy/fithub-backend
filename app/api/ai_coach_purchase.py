"""AI Coach purchase + program generation endpoint."""
import json
import os
import requests
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role

router = APIRouter(prefix="/ai-coach", tags=["ai-coach"])

AI_COACH_USER_ID = 60  # Special AI coach user in DB
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _call_claude(system_prompt: str, user_message: str) -> str:
    """Call Claude API for program generation."""
    if not ANTHROPIC_API_KEY:
        return ""
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-5-20241022",
                "max_tokens": 2000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            },
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json().get("content", [{}])[0].get("text", "")
    except Exception as e:
        print(f"[AI Coach] Claude error: {e}")
    return ""


@router.post("/purchase")
def purchase_ai_coach(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Purchase AI Coach package. Creates subscription, generates programs,
    updates client state to PROGRAM_ASSIGNED.
    """
    client_user_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. Check if already has AI coach subscription
        cur.execute(
            "SELECT id FROM subscriptions WHERE client_user_id = %s AND coach_user_id = %s AND status = 'active'",
            (client_user_id, AI_COACH_USER_ID),
        )
        if cur.fetchone():
            return {"ok": True, "message": "AI Koc zaten aktif"}

        # 2. Create subscription
        cur.execute(
            """
            INSERT INTO subscriptions (client_user_id, coach_user_id, plan_name, status, started_at, created_at, subscription_ref)
            VALUES (%s, %s, %s, 'active', NOW(), NOW(), %s)
            RETURNING id
            """,
            (client_user_id, AI_COACH_USER_ID, 'AI Koc', f'ai_coach_{client_user_id}_{int(datetime.utcnow().timestamp())}'),
        )
        sub_id = cur.fetchone()["id"]

        # 3. Get client onboarding data
        cur.execute("SELECT * FROM clients WHERE user_id = %s", (client_user_id,))
        client = cur.fetchone() or {}

        cur.execute("SELECT full_name, email FROM users WHERE id = %s", (client_user_id,))
        user = cur.fetchone() or {}

        # Get onboarding details
        gender = client.get("gender", "")
        weight = client.get("weight_kg", 70)
        height = client.get("height_cm", 175)
        goal = client.get("goal_type", "")
        experience = client.get("activity_level", "beginner")

        # 4. Generate workout program
        _generate_workout(cur, client_user_id, gender, weight, goal, experience)

        # 5. Generate nutrition program
        _generate_nutrition(cur, client_user_id, weight, goal)

        # 6. Generate cardio program
        _generate_cardio(cur, client_user_id, goal, experience)

        # 7. Update client state
        cur.execute(
            "UPDATE clients SET assigned_coach_id = %s WHERE user_id = %s",
            (AI_COACH_USER_ID, client_user_id),
        )

        # 8. Create conversation for AI chat
        cur.execute(
            """
            INSERT INTO conversations (client_user_id, coach_user_id, created_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT DO NOTHING
            """,
            (client_user_id, AI_COACH_USER_ID),
        )

        db.commit()

        return {
            "ok": True,
            "subscription_id": sub_id,
            "message": "AI Kocun aktif! Programlarin hazirlandi.",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI Coach purchase error: {str(e)}")


def _generate_workout(cur, client_user_id, gender, weight, goal, experience):
    """Generate and save workout program."""
    # Deactivate old programs
    cur.execute(
        "UPDATE workout_programs SET is_active = FALSE WHERE client_user_id = %s AND is_active = TRUE",
        (client_user_id,),
    )

    # Create program
    cur.execute(
        """
        INSERT INTO workout_programs (client_user_id, coach_user_id, title, is_active, created_at)
        VALUES (%s, %s, 'AI Antrenman Programi', TRUE, NOW())
        RETURNING id
        """,
        (client_user_id, AI_COACH_USER_ID),
    )
    program_id = cur.fetchone()["id"]

    # Exercise library lookup
    def _match_exercise(name):
        cur.execute(
            """SELECT id FROM exercise_library WHERE canonical_name ILIKE %s
               ORDER BY CASE WHEN canonical_name ILIKE %s THEN 0 ELSE 1 END, length(canonical_name) ASC LIMIT 1""",
            (f"%{name}%", f"{name}%"),
        )
        row = cur.fetchone()
        return row["id"] if row else None

    # Pre-built splits based on goal
    goal_l = (goal or "").lower()
    is_begin = "begin" in (experience or "").lower()

    if "lose" in goal_l or "weight" in goal_l:
        week = {
            "mon": {"title": "Tum Vucut A", "exercises": [
                ("Barbell Squat", "3", "12"), ("Dumbbell Bench Press", "3", "10"),
                ("Bent Over Barbell Row", "3", "10"), ("Mountain Climbers", "3", "30 sn"),
                ("Plank", "3", "45 sn"),
            ]},
            "wed": {"title": "Tum Vucut B", "exercises": [
                ("Leg Press", "3", "12"), ("Incline Dumbbell Press", "3", "10"),
                ("Dumbbell Incline Row", "3", "10"), ("Crunches", "3", "20"),
                ("Dead Bug", "3", "12"),
            ]},
            "fri": {"title": "Tum Vucut C", "exercises": [
                ("Barbell Squat", "3", "10"), ("Dumbbell Shoulder Press", "3", "12"),
                ("Dumbbell Bicep Curl", "3", "12"), ("Pushups", "3", "15"),
                ("Cable Russian Twists", "3", "15"),
            ]},
        }
    else:
        week = {
            "mon": {"title": "Push (Gogus/Omuz)", "exercises": [
                ("Dumbbell Bench Press", "4", "10"), ("Incline Dumbbell Press", "3", "10"),
                ("Dumbbell Shoulder Press", "3", "12"), ("Bench Dips", "3", "12"),
                ("Pushups", "3", "15"),
            ]},
            "tue": {"title": "Pull (Sirt/Biceps)", "exercises": [
                ("Bent Over Barbell Row", "4", "10"), ("Dumbbell Incline Row", "3", "10"),
                ("Dumbbell Bicep Curl", "3", "12"), ("Incline Dumbbell Flyes", "3", "12"),
            ]},
            "thu": {"title": "Legs (Bacak)", "exercises": [
                ("Barbell Squat", "4", "10"), ("Leg Press", "3", "12"),
                ("Leg Extensions", "3", "12"), ("Assisted Bulgarian Split Squat", "3", "10"),
                ("Standing Barbell Calf Raise", "4", "15"),
            ]},
            "fri": {"title": "Ust Vucut + Core", "exercises": [
                ("Dumbbell Bench Press", "3", "12"), ("Dumbbell Shoulder Press", "3", "12"),
                ("Dumbbell Bicep Curl", "3", "12"), ("Crunches", "3", "20"),
                ("Plank", "3", "60 sn"),
            ]},
        }

    day_keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    for idx, day_key in enumerate(day_keys):
        day_data = week.get(day_key)
        payload = None

        if day_data:
            items = []
            for ex_name, sets, reps in day_data["exercises"]:
                lib_id = _match_exercise(ex_name)
                items.append({"type": "exercise", "name": ex_name, "sets": sets, "reps": reps, "notes": ""})

                # Insert workout_exercise with library link
                cur.execute(
                    "SELECT id FROM workout_days WHERE workout_program_id = %s AND day_of_week = %s",
                    (program_id, day_key),
                )

            payload = {
                "title": day_data["title"],
                "coach_note": "",
                "warmup": {"duration_min": "", "items": []},
                "blocks": [{"title": "Workout Block", "items": items}],
            }

        cur.execute(
            """INSERT INTO workout_days (workout_program_id, day_of_week, order_index, day_payload)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (program_id, day_key, idx, json.dumps(payload) if payload else None),
        )
        day_id = cur.fetchone()["id"]

        # Insert exercises for linking
        if day_data:
            for ex_order, (ex_name, sets, reps) in enumerate(day_data["exercises"], 1):
                lib_id = _match_exercise(ex_name)
                cur.execute(
                    """INSERT INTO workout_exercises (workout_day_id, exercise_name, sets, reps, order_index, exercise_library_id)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (day_id, ex_name, int(sets), reps, ex_order, lib_id),
                )


def _generate_nutrition(cur, client_user_id, weight, goal):
    """Generate and save nutrition program."""
    cur.execute(
        "UPDATE nutrition_programs SET is_active = FALSE WHERE client_user_id = %s AND is_active = TRUE",
        (client_user_id,),
    )

    goal_l = (goal or "").lower()
    w = weight or 70
    calories = int(w * 30)
    if "lose" in goal_l:
        calories = int(w * 25)
    elif "gain" in goal_l or "muscle" in goal_l:
        calories = int(w * 35)

    cur.execute(
        """INSERT INTO nutrition_programs (client_user_id, coach_user_id, title, is_active, created_at)
           VALUES (%s, %s, 'AI Beslenme Programi', TRUE, NOW()) RETURNING id""",
        (client_user_id, AI_COACH_USER_ID),
    )
    prog_id = cur.fetchone()["id"]

    # Create meals for each day
    day_keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    for day in day_keys:
        meals = [
            (f"{day}:Kahvalti", "08:00", json.dumps([
                {"food_id": None, "name_tr": "Yulaf Ezmesi", "unit": "g", "amount": 80, "calories": int(calories * 0.12), "protein": 10, "carbs": 50, "fat": 5},
                {"food_id": None, "name_tr": "Yumurta", "unit": "adet", "amount": 3, "calories": int(calories * 0.08), "protein": 18, "carbs": 2, "fat": 12},
            ])),
            (f"{day}:Ogle Yemegi", "12:30", json.dumps([
                {"food_id": None, "name_tr": "Tavuk Gogsu", "unit": "g", "amount": 200, "calories": int(calories * 0.2), "protein": 45, "carbs": 0, "fat": 5},
                {"food_id": None, "name_tr": "Pilav", "unit": "g", "amount": 150, "calories": int(calories * 0.15), "protein": 5, "carbs": 55, "fat": 2},
            ])),
            (f"{day}:Aksam Yemegi", "19:00", json.dumps([
                {"food_id": None, "name_tr": "Somon", "unit": "g", "amount": 180, "calories": int(calories * 0.18), "protein": 35, "carbs": 0, "fat": 18},
                {"food_id": None, "name_tr": "Salata", "unit": "g", "amount": 200, "calories": int(calories * 0.05), "protein": 3, "carbs": 10, "fat": 5},
            ])),
        ]
        for meal_type, time, content in meals:
            cur.execute(
                """INSERT INTO nutrition_meals (nutrition_program_id, meal_type, content, planned_time, order_index)
                   VALUES (%s, %s, %s, %s, %s)""",
                (prog_id, meal_type, content, time, 0),
            )


def _generate_cardio(cur, client_user_id, goal, experience):
    """Generate and save cardio program."""
    cur.execute(
        "UPDATE cardio_programs SET is_active = FALSE WHERE client_user_id = %s AND is_active = TRUE",
        (client_user_id,),
    )

    cur.execute(
        """INSERT INTO cardio_programs (client_user_id, title, is_active, created_at)
           VALUES (%s, 'AI Kardiyo Programi', TRUE, NOW()) RETURNING id""",
        (client_user_id,),
    )
    prog_id = cur.fetchone()["id"]

    goal_l = (goal or "").lower()
    is_begin = "begin" in (experience or "").lower()

    sessions = []
    if "lose" in goal_l:
        sessions = [
            ("tue", "LISS", 20 if is_begin else 30, "Tempolu yuruyus veya hafif kosu"),
            ("thu", "HIIT", 15 if is_begin else 20, "30sn sprint / 60sn yuruyus"),
            ("sat", "LISS", 25 if is_begin else 40, "Uzun sureli duz tempo yuruyus"),
        ]
    else:
        sessions = [
            ("wed", "steady_state", 15 if is_begin else 20, "Orta tempo bisiklet veya kosu"),
            ("sat", "LISS", 20 if is_begin else 30, "Hafif yuruyus veya yuzmek"),
        ]

    for day, ctype, duration, notes in sessions:
        cur.execute(
            """INSERT INTO cardio_sessions (cardio_program_id, day_of_week, cardio_type, duration_min, notes, order_index)
               VALUES (%s, %s, %s, %s, %s, 0)""",
            (prog_id, day, ctype, duration, notes),
        )
