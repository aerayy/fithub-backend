"""AI Coach purchase + smart program generation.

v3 (2026-05-25): Workout uses the new rule-based pipeline (Phase A-E).
Nutrition stays on v2 (RAG + Constrained AI) since output quality was solid.

Flow:
  1. Idempotent check / exclusivity check
  2. Onboarding profile load
  3. Subscription create + assign AI Coach as student's coach (id=60)
  4. db.commit() so v3 pipeline + v2 nutrition endpoints see the assignment
  5. Parallel: nutrition v2 + workout v3 pipeline via asyncio.gather (~25-50s)
  6. Persist workout (v3 returns WeeklyProgram, we save_program it ourselves)
  7. Auto-activate (AI Coach skips manual coach approval)
  8. Cardio (heuristic) + conversation + final commit
"""
import asyncio
import json
import os
import math
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from app.services.badges import check_and_award
from app.services.workout import pipeline as workout_v3
from app.services.workout.persistence import save_program as save_workout_v3
from app.services.workout.validator import validate as validate_workout_v3
from app.services.workout.exercise_selector import select_candidates_for_session

router = APIRouter(prefix="/ai-coach", tags=["ai-coach"])

AI_COACH_USER_ID = 60


@router.post("/purchase")
async def purchase_ai_coach(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    # Late import to avoid circular dependency at module load
    from app.api.coach.routes import (
        generate_nutrition_program_v2,
    )

    client_user_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. Idempotent — already active?
        cur.execute(
            "SELECT id FROM subscriptions WHERE client_user_id = %s AND coach_user_id = %s AND status = 'active'",
            (client_user_id, AI_COACH_USER_ID),
        )
        if cur.fetchone():
            return {"ok": True, "message": "AI Koc zaten aktif", "already_active": True}

        # 2. Exclusivity — only one active coach at a time
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
                detail="Zaten bir koçla aktif aboneliğin var. AI Koç için önce mevcut aboneliğini iptal etmelisin.",
            )

        # 3. Onboarding profile (needed for cardio heuristic + summary)
        cur.execute("SELECT * FROM client_onboarding WHERE user_id = %s", (client_user_id,))
        ob = cur.fetchone() or {}
        cur.execute("SELECT * FROM clients WHERE user_id = %s", (client_user_id,))
        client = cur.fetchone() or {}

        profile = {
            "gender": ob.get("gender") or client.get("gender") or "Male",
            "age": ob.get("age") or 25,
            "weight_kg": float(ob.get("weight_kg") or client.get("weight_kg") or 75),
            "height_cm": int(ob.get("height_cm") or client.get("height_cm") or 175),
            "goal": ob.get("your_goal") or client.get("goal_type") or "gain_muscle",
            "experience": ob.get("experience") or "beginner",
            "workout_place": ob.get("workout_place") or ["gym"],
            "preferred_days": ob.get("preferred_workout_days") or [],
            "target_weight_kg": float(ob.get("target_weight_kg") or 0),
            "body_focus": ob.get("body_part_focus") or [],
        }

        # 4. Subscription + assigned_coach_id
        cur.execute(
            """INSERT INTO subscriptions (client_user_id, coach_user_id, plan_name, status,
               started_at, created_at, subscription_ref, program_assigned_at, program_state)
               VALUES (%s, %s, 'AI Koc', 'active', NOW(), NOW(), %s, NOW(), 'assigned') RETURNING id""",
            (client_user_id, AI_COACH_USER_ID, f'ai_coach_{client_user_id}_{int(datetime.utcnow().timestamp())}'),
        )
        sub_id = cur.fetchone()["id"]
        cur.execute(
            "UPDATE clients SET assigned_coach_id = %s WHERE user_id = %s",
            (AI_COACH_USER_ID, client_user_id),
        )
        # IMPORTANT: commit so v2 endpoints (which check assigned_coach_id=60) see this
        db.commit()

        # 5. Build payloads for v2 generators
        day_map = {
            "monday": "mon", "tuesday": "tue", "wednesday": "wed", "thursday": "thu",
            "friday": "fri", "saturday": "sat", "sunday": "sun",
            "pazartesi": "mon", "salı": "tue", "sali": "tue", "çarşamba": "wed",
            "carsamba": "wed", "perşembe": "thu", "persembe": "thu",
            "cuma": "fri", "cumartesi": "sat", "pazar": "sun",
        }
        training_days_short = []
        for d in (profile["preferred_days"] or []):
            key = day_map.get(str(d).lower().strip())
            if key and key not in training_days_short:
                training_days_short.append(key)
        if not training_days_short:
            # Sensible default: 3-day PPL
            training_days_short = ["mon", "wed", "fri"]

        nutrition_payload = {
            "meal_count": 5,
            "diet_type": "standard",
            "training_days": training_days_short,
            "include_supplements": True,
            "coach_notes": "AI Koç tarafından öğrencinin profiline göre üretildi.",
        }
        workout_payload = {
            "preferred_days": training_days_short,
        }

        # Fake "coach" current_user so v2 auth check passes (already-set assigned_coach_id=60)
        fake_coach_user = {"id": AI_COACH_USER_ID, "role": "coach", "email": "ai-coach@fithub.internal"}

        # 6. Parallel: nutrition v2 + workout v3 pipeline (~25-50s wall-clock)
        # v3 pipeline orchestrate çağırırken DB connection'i payload param'larıyla
        # tutarlı geçiyor; persist=False çünkü save_program'i biz ayrıca
        # çağıracağız (is_active=True ile, AI coach manuel onaya gerek yok).
        nutrition_task = generate_nutrition_program_v2(
            student_user_id=client_user_id,
            payload=nutrition_payload,
            db=db,
            current_user=fake_coach_user,
        )
        workout_task = workout_v3.orchestrate(
            conn=db,
            user_id=client_user_id,
            persist=False,
        )
        nutrition_result, workout_program = await asyncio.gather(
            nutrition_task, workout_task,
        )

        if not workout_program:
            raise HTTPException(status_code=502, detail="v3 pipeline returned no program")

        # 6b. v3 workout persistence + validation snapshot
        try:
            pools_by_day = {
                spec.day_index: select_candidates_for_session(db, spec, workout_program.profile)
                for spec in workout_program.split.sessions
            }
            v3_report = validate_workout_v3(workout_program, pools_by_day)
            v3_score = v3_report.score
        except Exception as _e:
            v3_score = None

        workout_program_id = save_workout_v3(
            db, workout_program,
            coach_user_id=AI_COACH_USER_ID,
            validation_score=v3_score,
            is_active=True,   # AI coach skips manual approval
        )

        # 7. Auto-activate nutrition (workout already active via save_workout_v3)
        nutrition_program_id = nutrition_result.get("program_id")
        if nutrition_program_id:
            cur.execute(
                "UPDATE nutrition_programs SET is_active = TRUE, updated_at = NOW() WHERE id = %s",
                (nutrition_program_id,),
            )

        # 8. Cardio (heuristic — no v2 generator yet)
        cardio_summary = _generate_cardio(cur, client_user_id, profile)

        # 9. Conversation
        cur.execute(
            "INSERT INTO conversations (client_user_id, coach_user_id, created_at) VALUES (%s, %s, NOW()) ON CONFLICT DO NOTHING",
            (client_user_id, AI_COACH_USER_ID),
        )

        db.commit()

        # 10. Badge (fail-safe)
        newly_earned = []
        try:
            newly_earned = check_and_award(client_user_id, "ai_coach_purchased", db)
        except Exception:
            pass

        # Build summary from v3 WeeklyProgram
        active_day_count = len(workout_program.sessions)
        ex_count = sum(len(s.exercises) for s in workout_program.sessions)
        workout_summary = {
            "days": active_day_count or len(training_days_short),
            "exercises": ex_count,
            "pipeline_version": "v3",
            "split_id": workout_program.split.split_id,
            "validation_score": v3_score,
        }

        week_n = nutrition_result.get("week", {})
        nutrition_meal_count = sum(
            len(meals) for meals in week_n.values() if isinstance(meals, list)
        )
        # Estimate daily kcal from monday (other days should be similar after v2 enforcement)
        mon_meals = week_n.get("mon", [])
        daily_kcal = 0
        for m in mon_meals:
            for item in (m.get("items") or []):
                try:
                    daily_kcal += float(item.get("calories") or 0)
                except (TypeError, ValueError):
                    pass
        nutrition_summary = {
            "calories": int(round(daily_kcal)),
            "meals": nutrition_meal_count,
            "rag_candidates": nutrition_result.get("rag_candidates", []),
            "enrichment": nutrition_result.get("enrichment", {}),
        }

        return {
            "ok": True,
            "subscription_id": sub_id,
            "message": "AI Koçun aktif! Programların hazırlandı.",
            "profile_summary": {
                "goal": _goal_label(profile["goal"]),
                "experience": _exp_label(profile["experience"]),
                "days": len(training_days_short),
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
        try:
            db.rollback()
        except Exception:
            pass
        raise
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        import logging
        logging.getLogger(__name__).exception("ai_coach_purchase: unexpected error")
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


# ─── Cardio (heuristic; no v2 generator) ───

def _generate_cardio(cur, client_user_id, profile):
    cur.execute(
        "UPDATE cardio_programs SET is_active = FALSE WHERE client_user_id = %s AND is_active = TRUE",
        (client_user_id,),
    )
    cur.execute(
        """INSERT INTO cardio_programs (client_user_id, coach_user_id, title, is_active, created_at)
           VALUES (%s, %s, 'AI Kardiyo Programi', TRUE, NOW()) RETURNING id""",
        (client_user_id, AI_COACH_USER_ID),
    )
    prog_id = cur.fetchone()["id"]

    goal_l = (profile["goal"] or "").lower()
    exp = (profile["experience"] or "").lower()
    is_begin = "begin" in exp

    if "lose" in goal_l:
        sessions = [
            ("tue", "LISS", 20 if is_begin else 30, "Tempolu yürüyüş veya hafif koşu"),
            ("thu", "HIIT", 15 if is_begin else 20, "30sn sprint / 60sn yürüyüş tekrarı"),
            ("sat", "LISS", 25 if is_begin else 40, "Uzun süreli düz tempo yürüyüş"),
        ]
    else:
        sessions = [
            ("wed", "steady_state", 15 if is_begin else 20, "Orta tempo bisiklet veya koşu"),
            ("sat", "LISS", 20 if is_begin else 30, "Hafif tempo yürüyüş"),
        ]

    for day, ctype, duration, notes in sessions:
        cur.execute(
            "INSERT INTO cardio_sessions (cardio_program_id, day_of_week, cardio_type, duration_min, notes, order_index) VALUES (%s,%s,%s,%s,%s,0)",
            (prog_id, day, ctype, duration, notes),
        )

    return {"sessions": len(sessions)}


# ─── Labels for response summary ───

def _goal_label(g):
    l = (g or "").lower()
    if "gain" in l or "muscle" in l:
        return "Kas Kazanımı"
    if "lose" in l or "weight" in l:
        return "Kilo Verme"
    if "tone" in l:
        return "Sıkılaşma"
    return "Fit Kalma"


def _exp_label(e):
    l = (e or "").lower()
    if "begin" in l:
        return "Başlangıç"
    if "year" in l or "intermediate" in l:
        return "Orta Seviye"
    if "advanced" in l:
        return "İleri"
    return "Orta Seviye"
