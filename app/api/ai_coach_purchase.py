"""AI Coach purchase + smart program generation based on onboarding data."""
import json
import os
import math
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from app.services.badges import check_and_award

router = APIRouter(prefix="/ai-coach", tags=["ai-coach"])

AI_COACH_USER_ID = 60


@router.post("/purchase")
def purchase_ai_coach(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    client_user_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        # Idempotent: AI Koç zaten aktifse OK dön
        cur.execute(
            "SELECT id FROM subscriptions WHERE client_user_id = %s AND coach_user_id = %s AND status = 'active'",
            (client_user_id, AI_COACH_USER_ID),
        )
        if cur.fetchone():
            return {"ok": True, "message": "AI Koc zaten aktif", "already_active": True}

        # Exclusivity: Regular koçtan aktif sub varsa reject — "one coach at a time".
        # Kullanıcı önce regular sub'ı cancel etsin, sonra AI alabilir.
        cur.execute(
            """
            SELECT id, coach_user_id FROM subscriptions
            WHERE client_user_id = %s AND status = 'active' AND coach_user_id != %s
            LIMIT 1
            """,
            (client_user_id, AI_COACH_USER_ID),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=409,
                detail="Zaten bir koçla aktif aboneliğin var. AI Koç için önce mevcut aboneliğini iptal etmelisin."
            )

        # Get full onboarding data
        cur.execute("SELECT * FROM client_onboarding WHERE user_id = %s", (client_user_id,))
        ob = cur.fetchone() or {}

        cur.execute("SELECT * FROM clients WHERE user_id = %s", (client_user_id,))
        client = cur.fetchone() or {}

        # Build user profile from onboarding
        profile = {
            "gender": ob.get("gender") or client.get("gender") or "Male",
            "age": ob.get("age") or 25,
            "weight_kg": float(ob.get("weight_kg") or client.get("weight_kg") or 75),
            "height_cm": int(ob.get("height_cm") or client.get("height_cm") or 175),
            "goal": ob.get("your_goal") or client.get("goal_type") or "gain_muscle",
            "body_type": ob.get("body_type") or "",
            "experience": ob.get("experience") or "beginner",
            "how_fit": ob.get("how_fit") or "",
            "knee_pain": ob.get("knee_pain") or "no",
            "pushups": ob.get("pushups") or "",
            "commit": ob.get("commit") or "least_3_months",
            "workout_length": ob.get("pref_workout_length") or "medium",
            "body_focus": ob.get("body_part_focus") or [],
            "workout_place": ob.get("workout_place") or ["gym"],
            "preferred_days": ob.get("preferred_workout_days") or [],
            "nutrition_budget": ob.get("nutrition_budget") or "",
            "target_weight_kg": float(ob.get("target_weight_kg") or 0),
        }

        # Create subscription
        cur.execute(
            """INSERT INTO subscriptions (client_user_id, coach_user_id, plan_name, status,
               started_at, created_at, subscription_ref, program_assigned_at, program_state)
               VALUES (%s, %s, 'AI Koc', 'active', NOW(), NOW(), %s, NOW(), 'assigned') RETURNING id""",
            (client_user_id, AI_COACH_USER_ID, f'ai_coach_{client_user_id}_{int(datetime.utcnow().timestamp())}'),
        )
        sub_id = cur.fetchone()["id"]

        # Generate programs
        workout_summary = _generate_workout(cur, client_user_id, profile)
        nutrition_summary = _generate_nutrition(cur, client_user_id, profile)
        cardio_summary = _generate_cardio(cur, client_user_id, profile)

        # Update client
        cur.execute("UPDATE clients SET assigned_coach_id = %s WHERE user_id = %s", (AI_COACH_USER_ID, client_user_id))

        # Create conversation
        cur.execute(
            "INSERT INTO conversations (client_user_id, coach_user_id, created_at) VALUES (%s, %s, NOW()) ON CONFLICT DO NOTHING",
            (client_user_id, AI_COACH_USER_ID),
        )

        db.commit()

        # Award AI coach badge (fail-safe)
        newly_earned = []
        try:
            newly_earned = check_and_award(client_user_id, 'ai_coach_purchased', db)
        except Exception:
            pass

        return {
            "ok": True,
            "subscription_id": sub_id,
            "message": "AI Koçun aktif! Programların hazırlandı.",
            "profile_summary": {
                "goal": _goal_label(profile["goal"]),
                "experience": _exp_label(profile["experience"]),
                "days": len(profile["preferred_days"]) if profile["preferred_days"] else 3,
                "focus": profile["body_focus"][:3] if profile["body_focus"] else [],
                "weight": profile["weight_kg"],
                "target_weight": profile["target_weight_kg"] if profile["target_weight_kg"] > 0 else None,
            },
            "workout_summary": workout_summary,
            "nutrition_summary": nutrition_summary,
            "cardio_summary": cardio_summary,
            "newly_earned": newly_earned,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


# ─── Workout Generation ───

def _generate_workout(cur, client_user_id, profile):
    cur.execute("UPDATE workout_programs SET is_active = FALSE WHERE client_user_id = %s AND is_active = TRUE", (client_user_id,))

    cur.execute(
        """INSERT INTO workout_programs (client_user_id, coach_user_id, title, is_active, created_at)
           VALUES (%s, %s, 'AI Antrenman Programi', TRUE, NOW()) RETURNING id""",
        (client_user_id, AI_COACH_USER_ID),
    )
    program_id = cur.fetchone()["id"]

    # Determine active days
    day_map = {"monday": "mon", "tuesday": "tue", "wednesday": "wed", "thursday": "thu",
               "friday": "fri", "saturday": "sat", "sunday": "sun"}
    active_days = [day_map.get(d.lower(), "") for d in (profile["preferred_days"] or []) if day_map.get(d.lower())]
    if not active_days:
        active_days = ["mon", "wed", "fri"]

    # Build splits considering all profile data
    has_knee_pain = profile["knee_pain"] != "no"
    is_home = "home" in [p.lower() for p in (profile["workout_place"] or [])] and "gym" not in [p.lower() for p in (profile["workout_place"] or [])]
    is_short = profile["workout_length"] == "short"
    focus = [f.lower() for f in (profile["body_focus"] or [])]

    splits = _build_smart_splits(len(active_days), profile["goal"], profile["experience"], has_knee_pain, is_home, is_short, focus)

    all_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    week = {}
    for i, day_key in enumerate(active_days):
        if i < len(splits):
            week[day_key] = splits[i]

    exercise_count = 0
    for idx, day_key in enumerate(all_days):
        day_data = week.get(day_key)
        payload = None
        if day_data:
            items = [{"type": "exercise", "name": n, "sets": s, "reps": r, "notes": ""} for n, s, r in day_data["exercises"]]
            payload = {
                "title": day_data["title"], "coach_note": "", "kcal": "",
                "warmup": {"duration_min": "", "items": []},
                "blocks": [{"title": "Workout Block", "items": items}],
            }
            exercise_count += len(items)

        cur.execute(
            "INSERT INTO workout_days (workout_program_id, day_of_week, order_index, day_payload) VALUES (%s, %s, %s, %s) RETURNING id",
            (program_id, day_key, idx, json.dumps(payload) if payload else None),
        )
        day_id = cur.fetchone()["id"]

        if day_data:
            for ex_order, (ex_name, sets, reps) in enumerate(day_data["exercises"], 1):
                lib_id = _match_exercise(cur, ex_name)
                cur.execute(
                    "INSERT INTO workout_exercises (workout_day_id, exercise_name, sets, reps, order_index, exercise_library_id) VALUES (%s,%s,%s,%s,%s,%s)",
                    (day_id, ex_name, int(sets), reps, ex_order, lib_id),
                )

    return {"days": len(active_days), "exercises": exercise_count}


def _build_smart_splits(day_count, goal, experience, has_knee_pain, is_home, is_short, focus):
    """Build personalized splits based on all onboarding parameters."""
    goal_l = (goal or "").lower()
    max_exercises = 4 if is_short else 5

    # Select exercises based on constraints
    squat = "Leg Press" if has_knee_pain else "Barbell Squat"
    lunge = "Leg Extensions" if has_knee_pain else "Assisted Bulgarian Split Squat"

    # Home vs gym exercises
    if is_home:
        chest = "Pushups"
        chest2 = "Push Up to Side Plank"
        back = "Dumbbell Incline Row"
        shoulder = "Dumbbell Shoulder Press"
        bicep = "Dumbbell Bicep Curl"
        tricep = "Bench Dips"
    else:
        chest = "Dumbbell Bench Press"
        chest2 = "Incline Dumbbell Press"
        back = "Bent Over Barbell Row"
        shoulder = "Dumbbell Shoulder Press"
        bicep = "Dumbbell Bicep Curl"
        tricep = "Bench Dips"

    # Extra focus exercises
    extra_chest = "Incline Dumbbell Flyes" if not is_home else "Pushups"
    extra_arms = bicep
    extra_core = "Crunches"
    extra_back = "Dumbbell Incline Row" if not is_home else "Dead Bug"

    # Check body focus priorities
    wants_chest = "chest" in focus
    wants_arms = "arms" in focus
    wants_belly = "belly" in focus or "core" in focus
    wants_back = "back" in focus

    if day_count <= 2:
        splits = [
            {"title": "Tum Vucut A", "exercises": [
                (squat, "3", "12"), (chest, "3", "10"), (back, "3", "10"),
                (shoulder, "3", "12"), ("Plank", "3", "45 sn"),
            ][:max_exercises]},
            {"title": "Tum Vucut B", "exercises": [
                ("Leg Press" if not has_knee_pain else "Leg Extensions", "3", "12"),
                (chest2, "3", "10"), (extra_back, "3", "10"),
                (bicep, "3", "12"), ("Crunches", "3", "20"),
            ][:max_exercises]},
        ]
    elif day_count == 3:
        if "lose" in goal_l:
            splits = [
                {"title": "Tum Vucut + Kardiyo", "exercises": [
                    (squat, "3", "15"), (chest, "3", "12"), (back, "3", "12"),
                    ("Mountain Climbers", "3", "30 sn"), ("Plank", "3", "45 sn"),
                ][:max_exercises]},
                {"title": "Ust Vucut + Core", "exercises": [
                    (chest2, "3", "12"), (shoulder, "3", "12"), (bicep, "3", "12"),
                    (tricep, "3", "12"), ("Cable Russian Twists", "3", "15"),
                ][:max_exercises]},
                {"title": "Alt Vucut + HIIT", "exercises": [
                    (squat, "3", "12"), ("Leg Press" if not has_knee_pain else "Leg Extensions", "3", "15"),
                    (lunge, "3", "10"), ("Pushups", "3", "15"), ("Dead Bug", "3", "12"),
                ][:max_exercises]},
            ]
        else:
            splits = [
                {"title": "Push (Gogus/Omuz)", "exercises": [
                    (chest, "4", "10"), (chest2, "3", "10"), (shoulder, "3", "12"), (tricep, "3", "12"),
                ][:max_exercises]},
                {"title": "Pull (Sirt/Biceps)", "exercises": [
                    (back, "4", "10"), (extra_back, "3", "10"), (bicep, "3", "12"),
                    (extra_chest if wants_chest else "Dead Bug", "3", "12"),
                ][:max_exercises]},
                {"title": "Legs (Bacak)", "exercises": [
                    (squat, "4", "10"), ("Leg Press", "3", "12"), (lunge, "3", "10"),
                    ("Standing Barbell Calf Raise" if not is_home else "Plank", "4", "15"),
                ][:max_exercises]},
            ]
    elif day_count == 4:
        splits = [
            {"title": "Gogus + Triceps", "exercises": [
                (chest, "4", "10"), (chest2, "3", "10"),
                (extra_chest if wants_chest else tricep, "3", "12"),
                (tricep, "3", "12"), ("Pushups" if wants_chest else "Plank", "3", "15"),
            ][:max_exercises]},
            {"title": "Sirt + Biceps", "exercises": [
                (back, "4", "10"), (extra_back, "3", "10"),
                (bicep, "4", "10"), (extra_arms if wants_arms else "Dead Bug", "3", "12"),
            ][:max_exercises]},
            {"title": "Bacak + Kalca", "exercises": [
                (squat, "4", "10"), ("Leg Press", "3", "12"), (lunge, "3", "10"),
                ("Leg Extensions", "3", "12"),
                ("Standing Barbell Calf Raise" if not is_home else "Mountain Climbers", "4", "15"),
            ][:max_exercises]},
            {"title": "Omuz + Core", "exercises": [
                (shoulder, "4", "10"), (bicep if wants_arms else "Plank", "3", "12"),
                (extra_core if wants_belly else tricep, "3", "20"),
                ("Cable Russian Twists" if wants_belly else "Plank", "3", "15"),
                ("Mountain Climbers", "3", "30 sn"),
            ][:max_exercises]},
        ]
    elif day_count == 5:
        splits = [
            {"title": "Gogus", "exercises": [(chest, "4", "10"), (chest2, "3", "10"), (extra_chest, "3", "12"), ("Pushups", "3", "15")][:max_exercises]},
            {"title": "Sirt", "exercises": [(back, "4", "10"), (extra_back, "3", "10"), ("Dead Bug", "3", "12")][:max_exercises]},
            {"title": "Omuz + Kol", "exercises": [(shoulder, "4", "10"), (bicep, "3", "12"), (tricep, "3", "12"), ("Cable Russian Twists", "3", "15")][:max_exercises]},
            {"title": "Bacak", "exercises": [(squat, "4", "10"), ("Leg Press", "3", "12"), (lunge, "3", "10"), ("Standing Barbell Calf Raise" if not is_home else "Plank", "4", "15")][:max_exercises]},
            {"title": "Tum Vucut + Core", "exercises": [(squat, "3", "12"), (chest, "3", "12"), (back, "3", "12"), ("Plank", "3", "60 sn"), (extra_core, "3", "20")][:max_exercises]},
        ]
    else:
        # 6-7 days PPL x2
        splits = [
            {"title": "Push A", "exercises": [(chest, "4", "10"), (chest2, "3", "10"), (shoulder, "3", "12"), (tricep, "3", "12")][:max_exercises]},
            {"title": "Pull A", "exercises": [(back, "4", "10"), (extra_back, "3", "10"), (bicep, "3", "12")][:max_exercises]},
            {"title": "Legs A", "exercises": [(squat, "4", "10"), ("Leg Press", "3", "12"), (lunge, "3", "10")][:max_exercises]},
            {"title": "Push B", "exercises": [(chest2, "4", "10"), ("Pushups", "3", "15"), (shoulder, "3", "12"), (extra_chest, "3", "12")][:max_exercises]},
            {"title": "Pull B", "exercises": [(extra_back, "4", "10"), (back, "3", "12"), (bicep, "3", "12"), ("Dead Bug", "3", "12")][:max_exercises]},
            {"title": "Legs B + Core", "exercises": [(squat, "3", "12"), (lunge, "3", "10"), ("Plank", "3", "60 sn"), (extra_core, "3", "20")][:max_exercises]},
            {"title": "Core + Mobilite", "exercises": [("Plank", "3", "60 sn"), ("Dead Bug", "3", "12"), ("Cable Russian Twists", "3", "15"), ("Mountain Climbers", "3", "30 sn")][:max_exercises]},
        ][:day_count]

    return splits


# ─── Nutrition Generation (Mifflin-St Jeor) ───

def _generate_nutrition(cur, client_user_id, profile):
    cur.execute("UPDATE nutrition_programs SET is_active = FALSE WHERE client_user_id = %s AND is_active = TRUE", (client_user_id,))

    # Mifflin-St Jeor TDEE calculation
    w = profile["weight_kg"]
    h = profile["height_cm"]
    age = profile["age"] if isinstance(profile["age"], int) else 25
    is_male = profile["gender"].lower() != "female"

    if is_male:
        bmr = 10 * w + 6.25 * h - 5 * age + 5
    else:
        bmr = 10 * w + 6.25 * h - 5 * age - 161

    # Activity multiplier based on experience
    exp = (profile["experience"] or "").lower()
    if "begin" in exp:
        multiplier = 1.4
    elif "year" in exp or "intermediate" in exp:
        multiplier = 1.55
    else:
        multiplier = 1.7

    tdee = bmr * multiplier

    # Goal adjustment
    goal_l = (profile["goal"] or "").lower()
    if "lose" in goal_l or "weight" in goal_l:
        calories = int(tdee - 400)  # deficit
    elif "gain" in goal_l or "muscle" in goal_l:
        calories = int(tdee + 300)  # surplus
    else:
        calories = int(tdee)

    # Macros
    protein = int(w * 2)  # 2g/kg
    fat = int(calories * 0.25 / 9)
    carbs = int((calories - protein * 4 - fat * 9) / 4)

    cur.execute(
        """INSERT INTO nutrition_programs (client_user_id, coach_user_id, title, is_active, created_at)
           VALUES (%s, %s, 'AI Beslenme Programi', TRUE, NOW()) RETURNING id""",
        (client_user_id, AI_COACH_USER_ID),
    )
    prog_id = cur.fetchone()["id"]

    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    meal_count = 0
    for day in days:
        meals = [
            (f"{day}:Kahvalti", "08:00", [
                {"food_id": None, "name_tr": "Yulaf Ezmesi", "unit": "g", "amount": 80, "calories": int(calories * 0.12), "protein": 10, "carbs": 50, "fat": 5},
                {"food_id": None, "name_tr": "Yumurta", "unit": "adet", "amount": 3, "calories": int(calories * 0.08), "protein": 18, "carbs": 2, "fat": 12},
            ]),
            (f"{day}:Ogle Yemegi", "12:30", [
                {"food_id": None, "name_tr": "Tavuk Gogsu", "unit": "g", "amount": 200, "calories": int(calories * 0.2), "protein": 45, "carbs": 0, "fat": 5},
                {"food_id": None, "name_tr": "Pilav", "unit": "g", "amount": 150, "calories": int(calories * 0.15), "protein": 5, "carbs": 55, "fat": 2},
                {"food_id": None, "name_tr": "Salata", "unit": "g", "amount": 150, "calories": int(calories * 0.03), "protein": 2, "carbs": 8, "fat": 3},
            ]),
            (f"{day}:Aksam Yemegi", "19:00", [
                {"food_id": None, "name_tr": "Somon", "unit": "g", "amount": 180, "calories": int(calories * 0.18), "protein": 35, "carbs": 0, "fat": 18},
                {"food_id": None, "name_tr": "Sebze", "unit": "g", "amount": 200, "calories": int(calories * 0.04), "protein": 3, "carbs": 10, "fat": 2},
            ]),
        ]
        for mt, time, items in meals:
            cur.execute(
                "INSERT INTO nutrition_meals (nutrition_program_id, meal_type, content, planned_time, order_index) VALUES (%s,%s,%s,%s,0)",
                (prog_id, mt, json.dumps(items), time),
            )
            meal_count += 1

    return {"calories": calories, "protein": protein, "carbs": carbs, "fat": fat, "meals": meal_count}


# ─── Cardio Generation ───

def _generate_cardio(cur, client_user_id, profile):
    cur.execute("UPDATE cardio_programs SET is_active = FALSE WHERE client_user_id = %s AND is_active = TRUE", (client_user_id,))

    cur.execute(
        """INSERT INTO cardio_programs (client_user_id, coach_user_id, title, is_active, created_at)
           VALUES (%s, %s, 'AI Kardiyo Programi', TRUE, NOW()) RETURNING id""",
        (client_user_id, AI_COACH_USER_ID),
    )
    prog_id = cur.fetchone()["id"]

    goal_l = (profile["goal"] or "").lower()
    exp = (profile["experience"] or "").lower()
    is_begin = "begin" in exp

    sessions = []
    if "lose" in goal_l:
        sessions = [
            ("tue", "LISS", 20 if is_begin else 30, "Tempolu yuruyus veya hafif kosu"),
            ("thu", "HIIT", 15 if is_begin else 20, "30sn sprint / 60sn yuruyus tekrari"),
            ("sat", "LISS", 25 if is_begin else 40, "Uzun sureli duz tempo yuruyus"),
        ]
    else:
        sessions = [
            ("wed", "steady_state", 15 if is_begin else 20, "Orta tempo bisiklet veya kosu"),
            ("sat", "LISS", 20 if is_begin else 30, "Hafif tempo yuruyus"),
        ]

    for day, ctype, duration, notes in sessions:
        cur.execute(
            "INSERT INTO cardio_sessions (cardio_program_id, day_of_week, cardio_type, duration_min, notes, order_index) VALUES (%s,%s,%s,%s,%s,0)",
            (prog_id, day, ctype, duration, notes),
        )

    return {"sessions": len(sessions)}


# ─── Helpers ───

def _match_exercise(cur, name):
    """Exercise name'i exercise_library'ye eşle, gif'li match döner.
    Match olmazsa Plank gibi safe fallback döner — NULL dönmez ki video boş kalmasın."""
    if not name:
        return _safe_fallback_id(cur)

    # 1) Exact match with gif
    cur.execute(
        """SELECT id FROM exercise_library
           WHERE canonical_name ILIKE %s
             AND gif_url IS NOT NULL AND gif_url != ''
           LIMIT 1""",
        (name,),
    )
    row = cur.fetchone()
    if row:
        return row["id"]

    # 2) Partial match with gif preference
    cur.execute(
        """SELECT id FROM exercise_library
           WHERE canonical_name ILIKE %s
             AND gif_url IS NOT NULL AND gif_url != ''
           ORDER BY CASE WHEN canonical_name ILIKE %s THEN 0 ELSE 1 END,
                    length(canonical_name) ASC
           LIMIT 1""",
        (f"%{name}%", f"{name}%"),
    )
    row = cur.fetchone()
    if row:
        return row["id"]

    # 3) Safe fallback — hiç bulunamazsa Plank veya benzeri
    return _safe_fallback_id(cur)


def _safe_fallback_id(cur):
    """Hiç match yoksa garantili gif'li bir hareket id'si dön (Plank tercih)."""
    for fallback_name in ("Plank", "Pushups", "Crunches"):
        cur.execute(
            """SELECT id FROM exercise_library
               WHERE canonical_name ILIKE %s
                 AND gif_url IS NOT NULL AND gif_url != ''
               LIMIT 1""",
            (fallback_name,),
        )
        row = cur.fetchone()
        if row:
            return row["id"]
    # Son çare: gif'i olan herhangi bir hareket
    cur.execute(
        "SELECT id FROM exercise_library WHERE gif_url IS NOT NULL AND gif_url != '' LIMIT 1"
    )
    row = cur.fetchone()
    return row["id"] if row else None


def _goal_label(g):
    l = (g or "").lower()
    if "gain" in l or "muscle" in l: return "Kas Kazanimi"
    if "lose" in l or "weight" in l: return "Kilo Verme"
    if "tone" in l: return "Sikilasma"
    return "Fit Kalma"


def _exp_label(e):
    l = (e or "").lower()
    if "begin" in l: return "Baslangic"
    if "year" in l or "intermediate" in l: return "Orta Seviye"
    if "advanced" in l: return "Ileri"
    return "Orta Seviye"
