from fastapi import APIRouter, Body, Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import json
import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
import psycopg2
from app.core.database import get_db
from app.core.security import require_role
from app.core.config import OPENAI_API_KEY
from app.api.coach.students import router as students_router
from app.api.coach.conversations import router as conversations_router
from app.api.coach.body_form import router as body_form_router
from app.api.coach.activity import router as activity_router
import re


def _match_exercise_library(cur, exercise_name: str):
    """Match exercise name to exercise_library, return (id, canonical_name, gif_url) or None.
    Prioritizes: exact match > word-overlap score > ILIKE contains.
    Always prefers exercises WITH gif_url."""
    if not exercise_name:
        return None

    name = exercise_name.strip()

    # 1. Exact match (case-insensitive)
    cur.execute(
        "SELECT id, canonical_name, gif_url FROM exercise_library WHERE canonical_name ILIKE %s LIMIT 1",
        (name,)
    )
    row = cur.fetchone()
    if row:
        return row

    # 2. Word-overlap scoring — split search into words, find best match
    raw_words = [w.lower() for w in re.sub(r'[^a-zA-Z0-9\s]', '', name).split() if len(w) > 2]
    # Simple stemming: remove trailing 's' for plural (Rows→Row, Curls→Curl, Flyes→Fly)
    words = []
    for w in raw_words:
        words.append(w)
        if w.endswith('s') and len(w) > 3:
            words.append(w[:-1])
        if w.endswith('es') and len(w) > 4:
            words.append(w[:-2])
        if w.endswith('ies') and len(w) > 5:
            words.append(w[:-3] + 'y')
    if words:
        like_params = [f"%{w}%" for w in words]
        score_expr = " + ".join(
            ["(CASE WHEN canonical_name ILIKE %s THEN 1 ELSE 0 END)"] * len(words)
        )
        threshold = max(2, len(words)) if len(words) >= 2 else 1
        # params: score_select, where_filter, order_score
        all_params = like_params + like_params + [threshold] + like_params
        cur.execute(
            f"""SELECT id, canonical_name, gif_url,
                       ({score_expr}) AS word_score
                FROM exercise_library
                WHERE ({score_expr}) >= %s
                ORDER BY
                  (gif_url IS NOT NULL AND gif_url != '') DESC,
                  ({score_expr}) DESC,
                  length(canonical_name) ASC
                LIMIT 1""",
            all_params,
        )
        row = cur.fetchone()
        if row:
            return row

    # 3. Fallback: every original word (or its stem) must appear
    if raw_words:
        # For each original word, create an OR group with its stem variants
        or_groups = []
        fb_params = []
        for w in raw_words:
            variants = {w}
            if w.endswith('s') and len(w) > 3:
                variants.add(w[:-1])
            if w.endswith('es') and len(w) > 4:
                variants.add(w[:-2])
            group = " OR ".join(["canonical_name ILIKE %s"] * len(variants))
            or_groups.append(f"({group})")
            fb_params.extend([f"%{v}%" for v in variants])
        where_clauses = " AND ".join(or_groups)
        cur.execute(
            f"""SELECT id, canonical_name, gif_url FROM exercise_library
                WHERE {where_clauses}
                ORDER BY (gif_url IS NOT NULL AND gif_url != '') DESC,
                         length(canonical_name) ASC
                LIMIT 1""",
            fb_params,
        )
        row = cur.fetchone()
        if row:
            return row

    # 4. Last resort: single ILIKE on full normalized name
    normalized = re.sub(r'\s*\([^)]*\)', '', name).strip()
    cur.execute(
        """SELECT id, canonical_name, gif_url FROM exercise_library
           WHERE canonical_name ILIKE %s
           ORDER BY (gif_url IS NOT NULL AND gif_url != '') DESC,
                    length(canonical_name) ASC
           LIMIT 1""",
        (f"%{normalized}%",)
    )
    return cur.fetchone()


router = APIRouter(prefix="/coach", tags=["coach"])
router.include_router(students_router)
router.include_router(conversations_router)
router.include_router(body_form_router)
router.include_router(activity_router)

# Predefined service tags (for future frontend use)
PREDEFINED_SERVICE_TAGS = [
    "7/24 Chat",
    "Form Analysis",
    "Nutrition Plan",
    "Personalized Workout",
    "Video Call",
    "1:1 Training",
    "Weekly Check-in",
    "Supplement Guidance",
    "Mobility/Stretching",
    "Progress Tracking"
]


def _fetchone_id(row):
    """tuple veya dict fetchone() uyumlu id okuyucu"""
    if row is None:
        return None
    if isinstance(row, dict):
        if "id" in row:
            return row["id"]
        return next(iter(row.values()))
    return row[0]


# --------------------------------------------------
# STUDENTS (LIST)
# --------------------------------------------------
@router.get("/students")
def get_my_students(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    cur = db.cursor()
    cur.execute(
        """
        SELECT
            u.id AS student_id,
            u.email,
            COALESCE(o.full_name, u.email) AS full_name,
            c.goal_type,
            c.activity_level,
            c.onboarding_done,
            c.created_at,

            s.plan_name,
            s.status AS subscription_status,
            s.purchased_at,
            s.started_at,
            s.ends_at,
            GREATEST(0, CEIL(EXTRACT(EPOCH FROM (s.ends_at - NOW())) / 86400))::int AS days_left
        FROM clients c
        JOIN users u ON u.id = c.user_id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        LEFT JOIN LATERAL (
            SELECT *
            FROM subscriptions
            WHERE client_user_id = u.id
              AND coach_user_id = c.assigned_coach_id
            ORDER BY purchased_at DESC NULLS LAST, id DESC
            LIMIT 1
        ) s ON TRUE
        WHERE c.assigned_coach_id = %s
        ORDER BY u.id;
        """,
        (current_user["id"],),
    )
    return {"students": cur.fetchall()}


# --------------------------------------------------
# ACTIVE PROGRAMS (READ)
# --------------------------------------------------
@router.get("/students/{student_user_id}/active-programs")
def get_active_programs(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # student ownership check
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # workout program (filtered by coach ownership)
    cur.execute(
        """
        SELECT id, client_user_id, title, is_active, created_at, updated_at
        FROM workout_programs
        WHERE client_user_id=%s AND coach_user_id=%s AND is_active=TRUE
        ORDER BY id DESC
        LIMIT 1
        """,
        (student_user_id, coach_id),
    )
    workout_program = cur.fetchone()

    workout_days = []
    workout_exercises = []

    if workout_program:
        program_id = workout_program["id"]
        cur.execute(
            """
            SELECT id, workout_program_id, day_of_week, order_index, created_at, updated_at
            FROM workout_days
            WHERE workout_program_id=%s
            ORDER BY order_index ASC, id ASC
            """,
            (program_id,),
        )
        workout_days = cur.fetchall()

        cur.execute(
            """
            SELECT
                e.id, e.workout_day_id, e.exercise_name, e.sets, e.reps, e.notes, e.order_index,
                e.created_at, e.updated_at, el.gif_url
            FROM workout_exercises e
            JOIN workout_days d ON d.id = e.workout_day_id
            LEFT JOIN exercise_library el ON el.id = e.exercise_library_id
            WHERE d.workout_program_id=%s
            ORDER BY d.order_index ASC, e.order_index ASC, e.id ASC
            """,
            (program_id,),
        )
        workout_exercises = cur.fetchall()

    # nutrition program (filtered by coach ownership)
    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, title, is_active, created_at, updated_at
        FROM nutrition_programs
        WHERE client_user_id=%s AND coach_user_id=%s AND is_active=TRUE
        ORDER BY id DESC
        LIMIT 1
        """,
        (student_user_id, coach_id),
    )
    nutrition_program = cur.fetchone()

    meals = []
    if nutrition_program:
        nutrition_program_id = nutrition_program["id"]
        cur.execute(
            """
            SELECT id, nutrition_program_id, meal_type, content, order_index, created_at, updated_at
            FROM nutrition_meals
            WHERE nutrition_program_id=%s
            ORDER BY order_index ASC, id ASC
            """,
            (nutrition_program_id,),
        )
        meals = cur.fetchall()

    # cardio program
    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, title, is_active, created_at, updated_at
        FROM cardio_programs
        WHERE client_user_id=%s AND is_active=TRUE
        ORDER BY id DESC
        LIMIT 1
        """,
        (student_user_id,),
    )
    cardio_program = cur.fetchone()

    cardio_sessions = []
    if cardio_program:
        cardio_program_id = cardio_program["id"]
        cur.execute(
            """
            SELECT id, cardio_program_id, day_of_week, cardio_type, duration_min, notes, order_index, created_at
            FROM cardio_sessions
            WHERE cardio_program_id=%s
            ORDER BY order_index ASC, id ASC
            """,
            (cardio_program_id,),
        )
        cardio_sessions = cur.fetchall()

    return {
        "workout_program": workout_program,
        "workout_days": workout_days,
        "workout_exercises": workout_exercises,
        "nutrition_program": nutrition_program,
        "meals": meals,
        "cardio_program": cardio_program,
        "cardio_sessions": cardio_sessions,
    }


# --------------------------------------------------
# WORKOUT PROGRAM SAVE
# --------------------------------------------------
def _flatten_day_to_exercises(day_data: dict) -> list:
    """
    Flatten a day payload (new format) into a list of exercise dicts for workout_exercises table.
    Handles warmup items and block items (including supersets).
    Returns list of {name, sets, reps, notes} dicts in order.
    """
    exercises = []
    
    # Warmup items first
    warmup = day_data.get("warmup", {}) or {}
    warmup_items = warmup.get("items", []) or []
    for item in warmup_items:
        if isinstance(item, dict):
            exercises.append({
                "name": item.get("name") or "",
                "sets": item.get("sets"),
                "reps": item.get("reps") or "",
                "notes": item.get("notes") or "",
            })
    
    # Block items
    blocks = day_data.get("blocks", []) or []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_items = block.get("items", []) or []
        for item in block_items:
            if not isinstance(item, dict):
                continue
            
            item_type = item.get("type", "exercise")
            
            if item_type == "exercise":
                exercises.append({
                    "name": item.get("name") or "",
                    "sets": item.get("sets"),
                    "reps": item.get("reps") or "",
                    "notes": item.get("notes") or "",
                })
            elif item_type == "superset":
                # Flatten superset items
                superset_items = item.get("items", []) or []
                for ss_item in superset_items:
                    if isinstance(ss_item, dict):
                        notes = ss_item.get("notes") or ""
                        # Optionally prefix with [SUPERSET] if notes exist
                        if notes:
                            notes = f"[SUPERSET] {notes}"
                        exercises.append({
                            "name": ss_item.get("name") or "",
                            "sets": ss_item.get("sets"),
                            "reps": ss_item.get("reps") or "",
                            "notes": notes,
                        })
    
    return exercises


@router.post("/students/{student_user_id}/workout-programs")
def save_workout_program(
    student_user_id: int,
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    try:
        # Create program as DRAFT (is_active=false)
        # Do NOT deactivate existing active program - that happens only on "Assign Program"
        cur.execute(
            """
            INSERT INTO workout_programs (client_user_id, coach_user_id, title, is_active)
            VALUES (%s, %s, %s, FALSE)
            RETURNING id
            """,
            (student_user_id, coach_id, "Coach Workout Program"),
        )
        program_id = _fetchone_id(cur.fetchone())

        week = payload.get("week", {}) or {}
        day_order = 1

        for day_key, day_value in week.items():
            if not day_value:
                continue

            # Detect format: old (array) vs new (object)
            is_old_format = isinstance(day_value, list)
            is_new_format = isinstance(day_value, dict)

            if not (is_old_format or is_new_format):
                continue

            # Prepare day_payload and exercises list
            day_payload_json = None
            exercises_to_insert = []

            if is_new_format:
                # New format: save day_payload JSONB
                day_payload_json = json.dumps(day_value)
                # Flatten to exercises for compatibility
                exercises_to_insert = _flatten_day_to_exercises(day_value)
            else:
                # Old format: array of exercises
                exercises_to_insert = day_value
                # Optionally generate minimal day_payload for backward compatibility
                # (We'll leave it NULL to maintain old behavior)

            # Insert workout_day
            cur.execute(
                """
                INSERT INTO workout_days (workout_program_id, day_of_week, order_index, day_payload)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (program_id, day_key, day_order, day_payload_json),
            )
            workout_day_id = _fetchone_id(cur.fetchone())

            # Insert exercises (for both old and new format)
            for ex_order, ex in enumerate(exercises_to_insert, start=1):
                if isinstance(ex, dict):
                    ex_name = ex.get("name") or ""
                    matched = _match_exercise_library(cur, ex_name)
                    lib_id = matched["id"] if matched else None
                    resolved_name = matched["canonical_name"] if matched else ex_name
                    cur.execute(
                        """
                        INSERT INTO workout_exercises
                        (workout_day_id, exercise_name, sets, reps, notes, order_index, exercise_library_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            workout_day_id,
                            resolved_name,
                            ex.get("sets"),
                            ex.get("reps") or "",
                            ex.get("notes") or "",
                            ex_order,
                            lib_id,
                        ),
                    )

            day_order += 1

        db.commit()
        return {"ok": True, "program_id": program_id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


def _normalize_reps(reps_value):
    """
    Normalize reps value for DB insert.
    Converts "8-10" -> 10, "8–10" (en-dash) -> 10, "AMRAP" -> None, "12" -> 12.
    Returns integer or None.
    """
    if reps_value is None:
        return None
    
    reps_str = str(reps_value).strip().upper()
    
    # Handle AMRAP, "to failure", etc.
    if any(keyword in reps_str for keyword in ["AMRAP", "FAILURE", "MAX", "AS MANY"]):
        return None
    
    # Handle range: "8-10" or "8–10" (en-dash)
    if "-" in reps_str or "–" in reps_str or "—" in reps_str:
        # Replace en-dash and em-dash with regular dash
        reps_str = reps_str.replace("–", "-").replace("—", "-")
        parts = reps_str.split("-")
        if len(parts) == 2:
            try:
                # Take the max value from range
                max_val = max(int(parts[0].strip()), int(parts[1].strip()))
                return max_val
            except (ValueError, IndexError):
                return None
    
    # Try to parse as integer
    try:
        return int(reps_str)
    except ValueError:
        return None


@router.post("/students/{student_user_id}/workout-programs/generate")
def generate_workout_program(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Generate a workout program using AI for a student.
    Creates a draft program (is_active=false) that can be assigned later.
    
    Example curl:
    curl -X POST "http://localhost:8000/coach/students/36/workout-programs/generate" \
      -H "Authorization: Bearer <coach_token>"
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # Check if student exists
    cur.execute(
        "SELECT id FROM users WHERE id=%s",
        (student_user_id,),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Student not found")

    # Fetch client onboarding data
    cur.execute(
        """
        SELECT
            co.age, co.weight_kg, co.height_cm, co.gender, co.your_goal,
            co.experience, co.how_fit, co.knee_pain, co.body_part_focus,
            co.pref_workout_length, co.workout_place, co.full_name,
            co.preferred_workout_days, co.target_weight_kg,
            u.email
        FROM client_onboarding co
        JOIN users u ON u.id = co.user_id
        WHERE co.user_id = %s
        """,
        (student_user_id,),
    )
    client_data = cur.fetchone()

    if not client_data:
        raise HTTPException(status_code=404, detail="Client onboarding data not found")

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        from openai import OpenAI
    except ImportError:
        raise HTTPException(status_code=500, detail="OpenAI library not installed.")

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # ── Extract onboarding data ──
        age = client_data.get("age") or "bilinmiyor"
        weight = client_data.get("weight_kg") or "bilinmiyor"
        height = client_data.get("height_cm") or "bilinmiyor"
        gender = client_data.get("gender") or "bilinmiyor"
        goal = client_data.get("your_goal") or "general fitness"
        experience = client_data.get("experience") or "beginner"
        fitness_level = client_data.get("how_fit") or "beginner"
        knee_pain = client_data.get("knee_pain")
        body_focus = client_data.get("body_part_focus")
        workout_length = client_data.get("pref_workout_length") or "medium"
        workout_place = client_data.get("workout_place")
        preferred_days = client_data.get("preferred_workout_days")
        target_weight = client_data.get("target_weight_kg")
        client_name = client_data.get("full_name") or ""

        # ── Parse preferred days ──
        day_map = {
            "Monday": "mon", "Tuesday": "tue", "Wednesday": "wed",
            "Thursday": "thu", "Friday": "fri", "Saturday": "sat", "Sunday": "sun",
        }
        day_names_tr = {
            "Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba",
            "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar",
        }
        if isinstance(preferred_days, list) and len(preferred_days) > 0:
            selected_keys = [day_map.get(d, d.lower()[:3]) for d in preferred_days if d in day_map]
            selected_names = [day_names_tr.get(d, d) for d in preferred_days if d in day_names_tr]
            days_instruction = f"Öğrenci şu günleri seçti: {', '.join(selected_names)}. SADECE bu günlere antrenman koy, diğer günler boş array olsun."
            num_days = len(selected_keys)
        else:
            days_instruction = "Öğrenci gün tercihi belirtmedi. Haftada 3-4 gün antrenman koy."
            num_days = 4

        # ── Parse workout place ──
        if isinstance(workout_place, list):
            places = ", ".join(workout_place) if workout_place else "gym"
        else:
            places = str(workout_place) if workout_place else "gym"

        place_equipment = {
            "gym": "Barbell, dumbbell, cable machine, smith machine, leg press ve tüm salon ekipmanları kullanılabilir.",
            "home": "Sadece bodyweight ve varsa dumbbell. Makine/barbell/cable hareketi KULLANMA.",
            "outdoor": "Bodyweight ağırlıklı, park barları kullanılabilir. Makine hareketi KULLANMA.",
        }
        equip_note = ""
        for p in (workout_place if isinstance(workout_place, list) else [str(workout_place or "gym")]):
            equip_note = place_equipment.get(p.lower().strip(), place_equipment["gym"])
            break

        # ── Parse workout length ──
        length_map = {"short": "30-40 dakika (4-5 hareket)", "medium": "45-60 dakika (5-7 hareket)", "long": "60-75 dakika (7-9 hareket)"}
        length_desc = length_map.get(str(workout_length).lower(), "45-60 dakika (5-7 hareket)")

        # ── Parse body focus ──
        focus_desc = ""
        if body_focus and isinstance(body_focus, list) and len(body_focus) > 0:
            focus_desc = f"Öğrenci şu bölgelere odaklanmak istiyor: {', '.join(body_focus)}. Bu bölgelere ekstra hacim ver."

        # ── Parse goal ──
        goal_map = {
            "lose_weight": "Kilo vermek — Kalori yakımını artıran, süperset ve devre antrenmanları tercih et. Dinlenme süreleri kısa (30-45sn).",
            "gain_muscle": "Kas geliştirmek — Ağır compound hareketler öncelikli, izolasyon ile destekle. Dinlenme 60-90sn.",
            "get_toned": "Sıkılaşmak — Orta ağırlık, yüksek tekrar. Compound + izolasyon dengeli. Dinlenme 45-60sn.",
        }
        goal_desc = goal_map.get(goal, "Genel fitness — dengeli bir program.")

        # ── Safety ──
        safety_note = ""
        if knee_pain and str(knee_pain).lower() in ("yes", "true", "1"):
            safety_note = "DİKKAT: Öğrencinin diz ağrısı var. Derin squat, lunge, leg press gibi diz baskılı hareketlerden KAÇIN. Üst vücut, core ve düşük etkili alt vücut hareketleri tercih et."

        # ── Experience mapping ──
        exp_map = {
            "no": "Hiç deneyimi yok — sadece temel, güvenli hareketler. Makine hareketleri tercih et.",
            "yes_year_ago": "1 yıl önce spor yapmış — temel hareketleri bilir, orta zorluk uygun.",
            "yes_more_year_ago": "Uzun süre önce yapmış — yeniden adapte olması lazım, orta-düşük zorluk.",
            "regular_exercise": "Düzenli egzersiz yapıyor — compound hareketler ve progressive overload uygun.",
        }
        exp_desc = exp_map.get(experience, "Başlangıç seviyesi — güvenli hareketler.")

        # ── Weight goal context ──
        weight_note = ""
        if target_weight and weight and weight != "bilinmiyor":
            try:
                diff = float(weight) - float(target_weight)
                if diff > 5:
                    weight_note = f"Öğrenci {diff:.0f} kg vermek istiyor ({weight}kg → {target_weight}kg)."
                elif diff < -5:
                    weight_note = f"Öğrenci {abs(diff):.0f} kg almak istiyor ({weight}kg → {target_weight}kg)."
            except (ValueError, TypeError):
                pass

        # ── Fetch exercises from DB — categorized ──
        cur.execute(
            """SELECT canonical_name, equipment, level, category, primary_muscles
               FROM exercise_library
               WHERE gif_url IS NOT NULL AND gif_url != ''
               ORDER BY
                 CASE WHEN level = 'beginner' THEN 0
                      WHEN level = 'intermediate' THEN 1
                      ELSE 2 END,
                 canonical_name""",
        )
        all_exercises = cur.fetchall()

        # Filter by workout place
        gym_equipment = {'dumbbell', 'barbell', 'cable', 'machine', 'body only', 'e-z curl bar', 'kettlebells', 'bands', 'other', 'medicine ball', 'exercise ball'}
        home_equipment = {'body only', 'dumbbell', 'bands', 'kettlebells'}
        outdoor_equipment = {'body only', 'bands'}

        if 'home' in places.lower():
            allowed_equip = home_equipment
        elif 'outdoor' in places.lower():
            allowed_equip = outdoor_equipment
        else:
            allowed_equip = gym_equipment

        filtered = [e for e in all_exercises if (e.get("equipment") or "").lower() in allowed_equip]
        exercise_names = [e["canonical_name"] for e in filtered]
        exercise_list_str = "\n".join(exercise_names)

        # RAG: Find similar client profiles and their real coach programs
        from app.services.rag_matcher import find_similar_programs, format_similar_programs_for_prompt

        target_for_rag = goal.replace("get_toned", "gain_muscle")  # normalize
        similar = find_similar_programs(
            age=int(age) if str(age).isdigit() else 25,
            weight=float(weight) if str(weight).replace('.', '').isdigit() else 70,
            height=float(height) if str(height).replace('.', '').isdigit() else 170,
            target=target_for_rag,
            gym="home" if "home" in str(places).lower() else "gym",
            activity="moderate",
            top_n=2,
            program_type="training",
        )
        coach_examples = format_similar_programs_for_prompt(similar, "training")

        # Fallback to static examples if RAG returns nothing
        if not coach_examples:
            try:
                examples_path = os.path.join(os.path.dirname(__file__), '../../data/coach_examples_for_prompt.txt')
                if os.path.exists(examples_path):
                    with open(examples_path, 'r', encoding='utf-8') as ef:
                        coach_examples = ef.read()
            except Exception:
                pass

        prompt = f"""Sen deneyimli bir fitness koçusun. Aşağıdaki öğrenci profiline göre KİŞİSELLEŞTİRİLMİŞ haftalık antrenman programı oluştur.

═══ ÖĞRENCİ PROFİLİ ═══
- İsim: {client_name or 'Belirtilmedi'}
- Yaş: {age} | Cinsiyet: {gender}
- Kilo: {weight} kg | Boy: {height} cm
- {weight_note}
- Hedef: {goal_desc}
- Deneyim: {exp_desc}
- Antrenman yeri: {places} → {equip_note}
- Tercih edilen antrenman süresi: {length_desc}
- {focus_desc}
{safety_note}

═══ GÜN TERCİHİ ═══
{days_instruction}

{coach_examples}

═══ EGZERSİZ VERİTABANI ═══
BİZİM DB'deki egzersiz isimlerinden SEÇ. İsim UYDURMA:

{exercise_list_str}

═══ PROGRAM YAZIM KURALLARI ═══
1. Egzersiz isimleri YUKARIDAKI VERİTABANI LİSTESİNDEN BİREBİR KOPYALANMALI
2. Kas grubu eşleştirmesi ÖRNEKLERE UYGUN olmalı:
   - 6 gün: Göğüs/Arka Kol → Sırt/Ön Kol → Omuz/Trapez → tekrar | Bacak ayrı gün
   - 5 gün: Göğüs/Arka Kol → Sırt/Ön Kol → Bacak → Omuz → Göğüs/Sırt (varyasyon)
   - 4 gün: Upper → Lower → Upper → Lower veya Push → Pull → Legs → Omuz
   - 3 gün: Full Body A → Full Body B → Full Body C veya Push/Pull/Legs
3. Her antrenman {length_desc} sürmeli
4. Sıralama: Compound → İzolasyon → Core/Mekik
5. Her günde 2-3 Birleşik Set (süperset) kullan — notes alanına "Birleşik Set" yaz
6. Set aralıkları: Compound 4-5×8-12, İzolasyon 3-4×12-15, Core 3-4×15-20
7. Notes alanına: RPE, tempo, teknik ipucu, veya "Birleşik Set" yaz
8. Popüler, temel hareketleri tercih et — garip/nadir hareketler KULLANMA

═══ ÇIKTI FORMATI ═══
Sadece JSON döndür:
{{
  "mon": [{{"name": "Exact Exercise Name", "sets": 3, "reps": "8-10", "notes": "RPE 7"}}],
  "tue": [],
  "wed": [],
  "thu": [],
  "fri": [],
  "sat": [],
  "sun": []
}}"""

        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen 10+ yıl deneyimli profesyonel bir fitness koçusun. Binlerce öğrenciye program yazmışsın. Öğrencinin profiline ve tercihlerine göre kişiselleştirilmiş, gerçek bir koçun yazacağı kalitede antrenman programları oluşturursun. Süperset kullanımı, doğru kas grubu eşleştirmesi ve egzersiz sıralaması konusunda uzmansın. Sadece JSON formatında yanıt ver."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.85,
        )

        # Parse response
        week_json_str = response.choices[0].message.content
        week_data = json.loads(week_json_str)

        # Validate structure and normalize
        week_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        week = {day: [] for day in week_days}
        
        for day_key in week_days:
            if day_key in week_data:
                day_exercises = week_data[day_key]
                if isinstance(day_exercises, list):
                    # Validate, normalize, and match to exercise_library
                    for ex in day_exercises:
                        if isinstance(ex, dict):
                            reps_raw = ex.get("reps", "8-10")
                            reps_str = str(reps_raw) if reps_raw else "8-10"
                            ai_name = str(ex.get("name", ""))

                            # Match to DB — get correct name + gif
                            matched = _match_exercise_library(cur, ai_name)
                            if matched:
                                resolved_name = matched["canonical_name"]
                                library_id = matched["id"]
                            else:
                                resolved_name = ai_name
                                library_id = None

                            week[day_key].append({
                                "name": resolved_name,
                                "sets": int(ex.get("sets", 3)) if ex.get("sets") else 3,
                                "reps": reps_str,
                                "notes": str(ex.get("notes", "")),
                                "library_id": library_id,
                            })

        # Find or create draft program (overwrite existing draft)
        cur.execute(
            """
            SELECT id FROM workout_programs
            WHERE client_user_id = %s AND coach_user_id = %s AND is_active = FALSE
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (student_user_id, coach_id),
        )
        existing_program = cur.fetchone()
        
        if existing_program:
            # Reuse existing draft program
            program_id = existing_program["id"]
            
            # Delete existing exercises and days
            cur.execute(
                """
                DELETE FROM workout_exercises
                WHERE workout_day_id IN (
                    SELECT id FROM workout_days WHERE workout_program_id = %s
                )
                """,
                (program_id,),
            )
            
            cur.execute(
                """
                DELETE FROM workout_days WHERE workout_program_id = %s
                """,
                (program_id,),
            )
        else:
            # Create new draft program
            cur.execute(
                """
                INSERT INTO workout_programs (client_user_id, coach_user_id, title, is_active)
                VALUES (%s, %s, %s, FALSE)
                RETURNING id
                """,
                (student_user_id, coach_id, "AI Workout Program"),
            )
            program_id = _fetchone_id(cur.fetchone())

        # Insert all 7 days (even if empty) with day_payload
        day_order = 1
        for day_key in week_days:
            exercises = week.get(day_key, [])
            
            # Build day_payload structure
            day_payload = None
            if exercises:
                day_payload = {
                    "title": "",
                    "kcal": "",
                    "coach_note": "",
                    "warmup": {
                        "duration_min": "",
                        "items": []
                    },
                    "blocks": [
                        {
                            "title": "Workout Block",
                            "items": [
                                {
                                    "type": "exercise",
                                    "name": ex.get("name", ""),
                                    "sets": ex.get("sets"),
                                    "reps": str(ex.get("reps", "")),
                                    "notes": ex.get("notes", ""),
                                }
                                for ex in exercises
                            ]
                        }
                    ]
                }
            
            # Insert workout_day (always insert, even if empty)
            cur.execute(
                """
                INSERT INTO workout_days (workout_program_id, day_of_week, order_index, day_payload)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (program_id, day_key, day_order, json.dumps(day_payload) if day_payload else None),
            )
            workout_day_id = _fetchone_id(cur.fetchone())

            # Insert exercises (only if day has exercises)
            if exercises:
                for ex_order, ex in enumerate(exercises, start=1):
                    reps_raw = ex.get("reps", "")
                    reps_db = str(reps_raw) if reps_raw else ""

                    sets_raw = ex.get("sets", 3)
                    try:
                        sets_db = int(sets_raw) if sets_raw else 3
                    except (ValueError, TypeError):
                        sets_db = 3

                    ex_name = str(ex.get("name", ""))

                    # Match to exercise_library for video + instructions
                    matched = _match_exercise_library(cur, ex_name)
                    lib_id = matched["id"] if matched else None
                    resolved_name = matched["canonical_name"] if matched else ex_name

                    cur.execute(
                        """
                        INSERT INTO workout_exercises
                        (workout_day_id, exercise_name, sets, reps, notes, order_index, exercise_library_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            workout_day_id,
                            resolved_name,
                            sets_db,
                            reps_db,
                            str(ex.get("notes", "")),
                            ex_order,
                            lib_id,
                        ),
                    )

            day_order += 1

        db.commit()
        
        # Log success
        logger = logging.getLogger(__name__)
        logger.info(f"AI workout draft created: program_id={program_id} student_id={student_user_id} coach_id={coach_id}")
        
        return {
            "program_id": program_id,
            "generated_by": "ai",
            "week": week
        }

    except json.JSONDecodeError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")
    except ImportError:
        db.rollback()
        raise HTTPException(status_code=500, detail="OpenAI library not installed. Please install openai package.")
    except Exception as e:
        db.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating workout program for student_id={student_user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


@router.get("/students/{student_user_id}/workout-programs/latest")
def get_latest_workout_program(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Get the latest saved workout program for a student (even if draft/not active).
    Returns UI-friendly flat structure for admin panel editor.
    
    Example curl:
    curl -X GET "http://localhost:8000/coach/students/36/workout-programs/latest" \
      -H "Authorization: Bearer <coach_token>"
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # Get latest program (by created_at DESC, then id DESC)
    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, title, is_active, created_at, updated_at
        FROM workout_programs
        WHERE client_user_id = %s AND coach_user_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (student_user_id, coach_id),
    )
    program = cur.fetchone()

    if not program:
        raise HTTPException(status_code=404, detail="Workout program not found")

    program_id = program["id"]
    is_active = bool(program["is_active"])

    # Get all days for this program
    cur.execute(
        """
        SELECT id, workout_program_id, day_of_week, order_index
        FROM workout_days
        WHERE workout_program_id = %s
        ORDER BY order_index ASC, id ASC
        """,
        (program_id,),
    )
    days = cur.fetchall() or []

    # Get all exercises grouped by workout_day_id
    day_ids = [d["id"] for d in days]
    exercises_by_day_id = {}
    
    if day_ids:
        placeholders = ",".join(["%s"] * len(day_ids))
        cur.execute(
            f"""
            SELECT we.id, we.workout_day_id, we.exercise_name, we.sets, we.reps,
                   we.notes, we.order_index, el.gif_url
            FROM workout_exercises we
            LEFT JOIN exercise_library el ON el.id = we.exercise_library_id
            WHERE we.workout_day_id IN ({placeholders})
            ORDER BY we.workout_day_id ASC, we.order_index ASC, we.id ASC
            """,
            tuple(day_ids),
        )
        all_exercises = cur.fetchall() or []
        
        for ex in all_exercises:
            day_id = ex["workout_day_id"]
            if day_id not in exercises_by_day_id:
                exercises_by_day_id[day_id] = []
            exercises_by_day_id[day_id].append(ex)

    # Build week structure: {mon: [], tue: [], ...}
    week_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    week = {day: [] for day in week_days}

    # Map days to week structure
    for day in days:
        day_key = day["day_of_week"]
        if day_key not in week_days:
            continue
        
        day_id = day["id"]
        exercises = exercises_by_day_id.get(day_id, [])
        
        # Convert exercises to flat format: {name, sets, reps, notes, gif_url}
        week[day_key] = [
            {
                "name": ex.get("exercise_name") or "",
                "sets": ex.get("sets"),
                "reps": ex.get("reps") or "",
                "notes": ex.get("notes") or "",
                **({"gif_url": ex["gif_url"]} if ex.get("gif_url") else {}),
            }
            for ex in exercises
        ]

    return {
        "program_id": program_id,
        "is_active": is_active,
        "week": week
    }


@router.post("/students/{student_user_id}/workout-programs/assign")
def assign_latest_workout_program(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Assign (activate) the latest workout program for a student.
    Reuses existing "set active" mechanism from assign_workout_program endpoint.
    
    Example curl:
    curl -X POST "http://localhost:8000/coach/students/36/workout-programs/assign" \
      -H "Authorization: Bearer <coach_token>"
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    try:
        # Find latest program for this student
        cur.execute(
            """
            SELECT id, client_user_id, coach_user_id, is_active
            FROM workout_programs
            WHERE client_user_id = %s AND coach_user_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (student_user_id, coach_id),
        )
        program = cur.fetchone()

        if not program:
            raise HTTPException(status_code=404, detail="Workout program not found")

        program_id = program["id"]

        # Reuse existing "set active" logic from assign_workout_program endpoint
        # 1. Deactivate all active programs for this student
        cur.execute(
            """
            UPDATE workout_programs
            SET is_active = FALSE, updated_at = NOW()
            WHERE client_user_id = %s AND is_active = TRUE
            """,
            (student_user_id,),
        )

        # 2. Activate the latest program
        cur.execute(
            """
            UPDATE workout_programs
            SET is_active = TRUE, updated_at = NOW()
            WHERE id = %s
            """,
            (program_id,),
        )

        # 3. Update program_assigned_at in subscriptions table (latest active/pending subscription)
        cur.execute(
            """
            UPDATE subscriptions
            SET program_assigned_at = NOW()
            WHERE id = (
                SELECT id
                FROM subscriptions
                WHERE client_user_id = %s
                  AND coach_user_id = %s
                  AND status IN ('pending', 'active')
                  AND (ends_at IS NULL OR ends_at > NOW())
                ORDER BY purchased_at DESC
                LIMIT 1
            )
            """,
            (student_user_id, coach_id),
        )

        db.commit()

        # Send push notification
        try:
            from app.services.push_notification import notify_program_assigned
            notify_program_assigned(student_user_id, "workout")
        except Exception:
            pass  # Don't fail the API call if notification fails

        return {"ok": True, "program_id": program_id}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


@router.post("/students/{student_user_id}/workout-programs/{program_id}/assign")
def assign_workout_program(
    student_user_id: int,
    program_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Assign (activate) a workout program for a student.
    This endpoint:
    1. Deactivates all currently active programs for the student
    2. Activates the specified program
    
    The program must belong to this coach and be for this student.
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    try:
        # Verify program exists, belongs to this coach, and is for this student
        cur.execute(
            """
            SELECT id, client_user_id, coach_user_id, is_active
            FROM workout_programs
            WHERE id = %s AND client_user_id = %s AND coach_user_id = %s
            """,
            (program_id, student_user_id, coach_id),
        )
        program = cur.fetchone()
        
        if not program:
            raise HTTPException(
                status_code=404,
                detail="Workout program not found or you don't have permission to assign it"
            )

        # Transaction: deactivate all active programs for this student, then activate the specified one
        cur.execute(
            """
            UPDATE workout_programs
            SET is_active = FALSE, updated_at = NOW()
            WHERE client_user_id = %s AND is_active = TRUE
            """,
            (student_user_id,),
        )

        cur.execute(
            """
            UPDATE workout_programs
            SET is_active = TRUE, updated_at = NOW()
            WHERE id = %s
            """,
            (program_id,),
        )

        # Update program_assigned_at in subscriptions table (latest active/pending subscription)
        cur.execute(
            """
            UPDATE subscriptions
            SET program_assigned_at = NOW()
            WHERE id = (
                SELECT id
                FROM subscriptions
                WHERE client_user_id = %s
                  AND coach_user_id = %s
                  AND status IN ('pending', 'active')
                  AND (ends_at IS NULL OR ends_at > NOW())
                ORDER BY purchased_at DESC
                LIMIT 1
            )
            """,
            (student_user_id, coach_id),
        )

        db.commit()
        return {"ok": True, "active_program_id": program_id}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


# --------------------------------------------------
# NUTRITION PROGRAM SAVE (MVP)
# --------------------------------------------------
@router.post("/students/{student_user_id}/nutrition-programs")
def save_nutrition_program(
    student_user_id: int,
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor()

    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    cur.execute(
        "UPDATE nutrition_programs SET is_active=FALSE WHERE client_user_id=%s AND is_active=TRUE",
        (student_user_id,),
    )

    cur.execute(
        """
        INSERT INTO nutrition_programs (client_user_id, coach_user_id, title, is_active)
        VALUES (%s, %s, %s, TRUE)
        RETURNING id
        """,
        (student_user_id, coach_id, "Coach Nutrition Program"),
    )
    nutrition_program_id = _fetchone_id(cur.fetchone())

    week = payload.get("week", {}) or {}
    week_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    order_counter = 0

    for day_key in week_days:
        day_meals = week.get(day_key) or []
        for idx, m in enumerate(day_meals, start=1):
            order_counter += 1
            meal_type = f"{day_key}:{idx}. Öğün"
            items = m.get("items") or []
            content = json.dumps(items)
            planned_time = m.get("time") or None

            cur.execute(
                """
                INSERT INTO nutrition_meals (nutrition_program_id, meal_type, content, order_index, planned_time)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nutrition_program_id, meal_type, content, order_counter, planned_time),
            )

    supplements = payload.get("supplements", [])
    if supplements:
        cur.execute(
            "UPDATE nutrition_programs SET supplements = %s::jsonb WHERE id = %s",
            (json.dumps(supplements), nutrition_program_id),
        )

    db.commit()
    return {"ok": True, "nutrition_program_id": nutrition_program_id}


@router.post("/students/{student_user_id}/nutrition-programs/generate")
def generate_nutrition_program(
    student_user_id: int,
    payload: dict = Body(...),
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # 1. Verify student is assigned to this coach
    cur.execute("SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s", (student_user_id, coach_id))
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Bu öğrenci size atanmamış")

    # 2. Fetch onboarding data first (needed for auto-macro calculation)
    cur.execute("""
        SELECT co.age, co.weight_kg, co.height_cm, co.gender, co.your_goal,
               COALESCE(co.full_name, u.full_name, u.email) AS client_name
        FROM client_onboarding co
        JOIN users u ON u.id = co.user_id
        WHERE co.user_id = %s
        ORDER BY co.id DESC LIMIT 1
    """, (student_user_id,))
    onb = cur.fetchone()

    age = onb.get("age", "bilinmiyor") if onb else "bilinmiyor"
    weight = onb.get("weight_kg", 70) if onb else 70
    height = onb.get("height_cm", 170) if onb else 170
    gender = onb.get("gender", "bilinmiyor") if onb else "bilinmiyor"
    goal = onb.get("your_goal", "genel sağlık") if onb else "genel sağlık"

    # 3. Get form inputs from coach
    meal_count = payload.get("meal_count", 5)
    diet_type = payload.get("diet_type", "standard")
    training_days = payload.get("training_days", [])
    include_supplements = payload.get("include_supplements", True)
    coach_notes = payload.get("coach_notes", "")

    # 4. Get target macros from payload OR auto-calculate
    target_calories = payload.get("target_calories")
    target_protein = payload.get("target_protein")
    target_carbs = payload.get("target_carbs")
    target_fat = payload.get("target_fat")

    w = float(weight) if weight != "bilinmiyor" else 70
    h = float(height) if height != "bilinmiyor" else 170
    a = int(age) if age != "bilinmiyor" else 25
    g = str(gender).lower()
    gl = str(goal).lower()

    if not all([target_calories, target_protein, target_carbs, target_fat]):
        if g in ("female", "kadın"):
            bmr = 10 * w + 6.25 * h - 5 * a - 161
        else:
            bmr = 10 * w + 6.25 * h - 5 * a + 5

        tdee = bmr * 1.55
        if "lose" in gl or "weight" in gl:
            target_calories = int(tdee * 0.8)
        elif "gain" in gl or "muscle" in gl:
            target_calories = int(tdee * 1.15)
        else:
            target_calories = int(tdee)

        # Adjust macros by diet type
        if diet_type == "high_protein":
            target_protein = int(w * 2.5)
        elif diet_type == "keto":
            target_protein = int(w * 2)
        else:
            target_protein = int(w * 2)

        if diet_type == "keto":
            target_carbs = int(target_calories * 0.05 / 4)
            target_fat = int((target_calories - target_protein * 4 - target_carbs * 4) / 9)
        elif diet_type == "low_carb":
            target_carbs = int(target_calories * 0.15 / 4)
            target_fat = int((target_calories - target_protein * 4 - target_carbs * 4) / 9)
        else:
            target_fat = int(target_calories * 0.25 / 9)
            target_carbs = int((target_calories - target_protein * 4 - target_fat * 9) / 4)

    client_name = onb.get("client_name", "Danışan") if onb else "Danışan"

    # 4. Fetch food database for AI prompt
    cur.execute("""
        SELECT
            COALESCE(fl.name_tr, fi.name_en) AS name,
            fi.serving_unit,
            fn.calories_kcal AS cal,
            fn.protein_g AS prot,
            fn.fat_g AS fat,
            fn.carbs_g AS carb
        FROM food_items fi
        JOIN food_nutrients_100g fn ON fn.food_id = fi.id
        LEFT JOIN food_localization_tr fl ON fl.food_id = fi.id
        WHERE fi.source = 'begreens'
        ORDER BY fi.id
    """)
    db_foods = cur.fetchall() or []

    # Build compact food list for prompt
    food_lines = []
    for f in db_foods:
        name = f["name"] or ""
        unit = f.get("serving_unit") or "g"
        cal = f.get("cal") or 0
        prot = f.get("prot") or 0
        fat = f.get("fat") or 0
        carb = f.get("carb") or 0
        if unit == "g":
            food_lines.append(f"{name} | 100g: {cal}kcal P:{prot} C:{carb} F:{fat}")
        else:
            food_lines.append(f"{name} | 1 {unit}: {cal}kcal P:{prot} C:{carb} F:{fat}")

    food_catalog = "\n".join(food_lines)

    # RAG: Find similar profiles for nutrition examples
    from app.services.rag_matcher import find_similar_programs, format_similar_programs_for_prompt

    target_for_rag = str(goal).lower().replace("genel sağlık", "maintain")
    if "lose" in target_for_rag or "kilo ver" in target_for_rag:
        target_for_rag = "lose_weight"
    elif "gain" in target_for_rag or "kas" in target_for_rag:
        target_for_rag = "gain_muscle"

    similar_nutr = find_similar_programs(
        age=int(age) if str(age).isdigit() else 25,
        weight=float(w),
        height=float(h),
        target=target_for_rag,
        gym="gym",
        activity="moderate",
        top_n=2,
        program_type="nutrition",
    )
    nutrition_examples = format_similar_programs_for_prompt(similar_nutr, "nutrition")

    # Fallback to static examples
    if not nutrition_examples:
        try:
            ex_path = os.path.join(os.path.dirname(__file__), '../../data/nutrition_examples_for_prompt.txt')
            if os.path.exists(ex_path):
                with open(ex_path, 'r', encoding='utf-8') as ef:
                    nutrition_examples = ef.read()
        except Exception:
            pass

    # Diet type descriptions
    diet_descs = {
        "standard": "Standart dengeli beslenme",
        "high_protein": "Yüksek proteinli — protein ağırlıklı, her öğünde protein kaynağı olmalı",
        "low_carb": "Düşük karbonhidrat — pirinç/makarna/ekmek minimumda, sebze ve protein ağırlıklı",
        "keto": "Ketojenik — karbonhidrat çok düşük (<30g/gün), yağ yüksek, tahıl/meyve/şeker yok",
        "vegetarian": "Vejetaryen — et/tavuk/balık yok, yumurta ve süt ürünleri kullanılabilir",
    }
    diet_desc = diet_descs.get(diet_type, "Standart dengeli beslenme")

    # Training days instruction
    training_note = ""
    if training_days:
        day_names = {"mon": "Pazartesi", "tue": "Salı", "wed": "Çarşamba", "thu": "Perşembe", "fri": "Cuma", "sat": "Cumartesi", "sun": "Pazar"}
        tr_days = [day_names.get(d, d) for d in training_days]
        training_note = f"""
ANTRENMANLı GÜNLER: {', '.join(tr_days)}
- Antrenman günlerinde: Spordan 1.5-2 saat önce karbonhidrat ağırlıklı öğün, spordan sonra protein ağırlıklı öğün
- Dinlenme günlerinde: Karbonhidrat %15-20 düşür, yağ biraz artır"""

    # Supplement note
    supplement_note = ""
    if include_supplements:
        supplement_note = """
SUPPLEMENT ÖNERİLERİ EKLENMELİ:
- Kahvaltıdan sonra: Multivitamin, C vitamini
- Spordan 30dk önce: L-Carnitine veya Kafein
- Spordan sonra: Whey Protein, BCAA veya Glutamine
- Yatmadan önce: ZMA veya Kazein (opsiyonel)
Supplement'leri ilgili öğüne ekle, makro değerleri 0 yaz."""

    # Coach notes
    coach_note = f"\nKOÇUN NOTU: {coach_notes}" if coach_notes else ""

    prompt = f"""Sen Türkiye'de çalışan, binlerce danışana program yazmış profesyonel bir beslenme koçusun.

═══ DANIŞAN PROFİLİ ═══
- İsim: {client_name}
- Yaş: {age} | Cinsiyet: {gender}
- Kilo: {weight} kg | Boy: {height} cm
- Hedef: {goal}
- Diyet tipi: {diet_desc}

═══ GÜNLÜK HEDEF MAKROLAR ═══
- Kalori: {target_calories} kcal
- Protein: {target_protein}g
- Karbonhidrat: {target_carbs}g
- Yağ: {target_fat}g
{training_note}
{supplement_note}
{coach_note}

═══ GERÇEK KOÇ BESLENME PROGRAMI ÖRNEKLERİ ═══
Aşağıda profesyonel bir koçun gerçek danışanlarına yazdığı beslenme programları var.
BU ÖĞÜN YAPISINI VE ZAMANLAMASINI TAKLİT ET:
- "KAHVALTIDAN ÖNCE YAPILACAK" (soda+limon+sirke gibi detoks)
- "1. ÖĞÜN KAHVALTI"
- "KAHVALTIDAN SONRA ALINACAKLAR" (vitaminler)
- "2. ÖĞÜN" / "3. ÖĞÜN" (ana öğünler)
- "SPORDAN 1.5 SAAT ÖNCE" (karbonhidrat ağırlıklı)
- "SPORDAN SONRA ALINACAKLAR" (protein shake, BCAA)
- "GECE YATMADAN ÖNCE" (kazein veya hafif atıştırma)

{nutrition_examples}

═══ BESİN VERİTABANI ═══
SADECE bu listeden seç, isim UYDURMA:

{food_catalog}

═══ PROGRAM KURALLARI ═══
1. Her gün {meal_count} öğün — koç örneklerindeki gibi isimlendir
2. Besin isimleri VERİTABANINDAN BİREBİR KOPYALANMALI
3. KRİTİK: Her öğünde EN AZ 3-5 BESİN olmalı — tek besin koyma! Gerçek bir yemek tabağı gibi düşün:
   - Protein kaynağı (et/tavuk/balık/yumurta)
   - Karbonhidrat kaynağı (pirinç/makarna/patates/ekmek)
   - Sebze/salata
   - Yağ kaynağı (zeytinyağı/ceviz/avokado)
4. Birim "g" olanlarda miktarı gram olarak yaz (50, 100, 150, 200 gibi)
5. Birim "adet/porsiyon/dilim" olanlarda adedi yaz
6. Günler arası çeşitlilik sağla — aynı yemeği her gün koyma
7. Türk mutfağına uygun, pratik yemekler
8. Saatler gerçekçi olsun (07:00 - 23:00 arası)
9. Makro hesabı YAPMA — sadece isim ve miktar yaz, makroyu biz hesaplarız

═══ ÇIKTI FORMATI ═══
Sadece JSON döndür. MAKRO YAZMA, sadece isim ve miktar:
{{
  "week": {{
    "mon": {{
      "meals": [
        {{
          "type": "1. ÖĞÜN KAHVALTI",
          "time": "08:00",
          "items": [
            {{"name_tr": "Yumurta Beyazı", "amount": 5, "unit": "adet"}},
            {{"name_tr": "Yumurta Sarısı", "amount": 2, "unit": "adet"}},
            {{"name_tr": "Basmati Pirinç", "amount": 80, "unit": "g"}},
            {{"name_tr": "Sebze Salatası", "amount": 40, "unit": "g"}},
            {{"name_tr": "Zeytin yağı", "amount": 1, "unit": "Yemek Kaşığı"}}
          ]
        }}
      ]
    }},
    "tue": {{}}, "wed": {{}}, "thu": {{}}, "fri": {{}}, "sat": {{}}, "sun": {{}}
  }}
}}"""

    # 5. Call OpenAI
    from openai import OpenAI as _OpenAI

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        ai_client = _OpenAI(api_key=OPENAI_API_KEY)
        response = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen Türkiye'de 10+ yıl deneyimli, binlerce danışana beslenme programı yazmış profesyonel bir beslenme koçusun. Türk mutfağına uygun, pratik, makro hedeflerine birebir uyan ve gerçek koç kalitesinde haftalık beslenme programları hazırlıyorsun. Öğün zamanlaması, antrenman günü/dinlenme günü ayrımı ve supplement yerleştirme konusunda uzmansın. Sadece JSON formatında yanıt ver."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )
        result = json.loads(response.choices[0].message.content)
        week_data = result.get("week", {})

        # Build food lookup from DB for macro calculation
        food_lookup = {}
        for f in db_foods:
            name = (f["name"] or "").strip().lower()
            if name:
                food_lookup[name] = {
                    "cal": float(f.get("cal") or 0),
                    "prot": float(f.get("prot") or 0),
                    "carb": float(f.get("carb") or 0),
                    "fat": float(f.get("fat") or 0),
                    "unit": f.get("serving_unit") or "g",
                }

        # Enrich AI output with calculated macros from DB
        for day_key, day_data in week_data.items():
            if not isinstance(day_data, dict):
                continue
            for meal in day_data.get("meals", []):
                for item in meal.get("items", []):
                    name_tr = (item.get("name_tr") or "").strip()
                    lookup_key = name_tr.lower()
                    db_food = food_lookup.get(lookup_key)

                    if db_food:
                        amount = float(item.get("amount") or item.get("grams") or 100)
                        unit = item.get("unit") or db_food["unit"]

                        if unit == "g":
                            ratio = amount / 100.0
                        else:
                            ratio = amount  # adet/porsiyon — makrolar zaten 1 birim için

                        item["grams"] = amount
                        item["calories"] = round(db_food["cal"] * ratio, 1)
                        item["protein"] = round(db_food["prot"] * ratio, 1)
                        item["carbs"] = round(db_food["carb"] * ratio, 1)
                        item["fat"] = round(db_food["fat"] * ratio, 1)
                    else:
                        # Not found in DB — keep as is with 0 macros
                        item["grams"] = float(item.get("amount") or item.get("grams") or 0)
                        item.setdefault("calories", 0)
                        item.setdefault("protein", 0)
                        item.setdefault("carbs", 0)
                        item.setdefault("fat", 0)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")

    if not week_data:
        raise HTTPException(status_code=500, detail="AI boş bir program döndürdü")

    # 6. Save and activate (deactivate old, activate new)
    try:
        # Deactivate all active nutrition programs for this student
        cur.execute(
            "UPDATE nutrition_programs SET is_active = FALSE, updated_at = NOW() WHERE client_user_id = %s AND is_active = TRUE",
            (student_user_id,),
        )

        # Check for existing draft to reuse
        cur.execute("""
            SELECT id FROM nutrition_programs
            WHERE client_user_id = %s AND coach_user_id = %s AND is_active = FALSE
            ORDER BY created_at DESC LIMIT 1
        """, (student_user_id, coach_id))
        existing = cur.fetchone()

        if existing:
            program_id = existing["id"]
            cur.execute("DELETE FROM nutrition_meals WHERE nutrition_program_id = %s", (program_id,))
            cur.execute("UPDATE nutrition_programs SET is_active = TRUE, updated_at = NOW(), title = 'AI Beslenme Programı' WHERE id = %s", (program_id,))
        else:
            cur.execute("""
                INSERT INTO nutrition_programs (client_user_id, coach_user_id, title, is_active, created_at, updated_at)
                VALUES (%s, %s, 'AI Beslenme Programı', TRUE, NOW(), NOW())
                RETURNING id
            """, (student_user_id, coach_id))
            row = cur.fetchone()
            program_id = row["id"] if isinstance(row, dict) else row[0]

        # Insert meals per day — day_key stored in meal_type as "mon:1. Öğün"
        week_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        order_counter = 0
        for day_key in week_days:
            day_data = week_data.get(day_key, {})
            day_meals = day_data.get("meals", []) if isinstance(day_data, dict) else []
            for idx, meal in enumerate(day_meals, start=1):
                order_counter += 1
                meal_type = f"{day_key}:{idx}. Öğün"
                items = meal.get("items", [])
                content = json.dumps(items)
                planned_time = meal.get("time")
                cur.execute("""
                    INSERT INTO nutrition_meals (nutrition_program_id, meal_type, content, order_index, planned_time, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """, (program_id, meal_type, content, order_counter, planned_time))

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")

    # 7. Build response — week with per-day meals
    response_week = {}
    for day_key in week_days:
        day_data = week_data.get(day_key, {})
        day_meals = day_data.get("meals", []) if isinstance(day_data, dict) else []
        response_week[day_key] = [
            {"type": f"{i}. Öğün", "time": m.get("time", ""), "items": m.get("items", [])}
            for i, m in enumerate(day_meals, start=1)
        ]

    return {
        "program_id": program_id,
        "generated_by": "ai",
        "week": response_week
    }


@router.get("/students/{student_user_id}/nutrition-programs/latest")
def get_latest_nutrition_program(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Get the latest saved nutrition program for a student.
    Returns UI-friendly structure with week (all days share the same meals).
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # Get latest nutrition program
    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, title, is_active, supplements, created_at, updated_at
        FROM nutrition_programs
        WHERE client_user_id = %s AND coach_user_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (student_user_id, coach_id),
    )
    program = cur.fetchone()

    if not program:
        raise HTTPException(status_code=404, detail="Nutrition program not found")

    program_id = program["id"]
    is_active = bool(program["is_active"])
    title = program.get("title") or ""
    generated_by = "ai" if "AI" in title else None
    supplements = program.get("supplements") or []

    # Get all meals for this program
    cur.execute(
        """
        SELECT id, meal_type, content, order_index, planned_time
        FROM nutrition_meals
        WHERE nutrition_program_id = %s
        ORDER BY order_index ASC, id ASC
        """,
        (program_id,),
    )
    meals_rows = cur.fetchall() or []

    # Build meals per day
    week_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    week = {day: [] for day in week_days}

    for m in meals_rows:
        raw_content = m.get("content") or "[]"
        if isinstance(raw_content, str):
            try:
                items = json.loads(raw_content)
            except (json.JSONDecodeError, TypeError):
                items = []
        else:
            items = raw_content

        meal_type_raw = m.get("meal_type") or ""
        planned_time = m.get("planned_time") or ""

        # Parse "day_key:meal_type" format (e.g. "mon:1. Öğün")
        if ":" in meal_type_raw:
            day_key, meal_type = meal_type_raw.split(":", 1)
            if day_key in week:
                week[day_key].append({"type": meal_type, "time": planned_time, "items": items})
        else:
            # Legacy format — assign to all days
            meal_obj = {"type": meal_type_raw, "time": planned_time, "items": items}
            for day in week_days:
                week[day].append(meal_obj)

    return {
        "program_id": program_id,
        "is_active": is_active,
        "generated_by": generated_by,
        "supplements": supplements,
        "week": week,
    }


@router.delete("/students/{student_user_id}/workout-programs/{program_id}")
def delete_workout_program(
    student_user_id: int,
    program_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Delete a workout program and all its associated days and exercises.
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # Get day ids for this program
    cur.execute(
        "SELECT id FROM workout_days WHERE workout_program_id = %s",
        (program_id,),
    )
    day_rows = cur.fetchall() or []
    day_ids = [d["id"] for d in day_rows]

    # Delete exercises for those days
    if day_ids:
        placeholders = ",".join(["%s"] * len(day_ids))
        cur.execute(
            f"DELETE FROM workout_exercises WHERE workout_day_id IN ({placeholders})",
            tuple(day_ids),
        )

    # Delete days
    cur.execute(
        "DELETE FROM workout_days WHERE workout_program_id = %s",
        (program_id,),
    )

    # Delete program
    cur.execute(
        "DELETE FROM workout_programs WHERE id = %s",
        (program_id,),
    )

    db.commit()
    return {"ok": True}


@router.delete("/students/{student_user_id}/nutrition-programs/{program_id}")
def delete_nutrition_program(
    student_user_id: int,
    program_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Delete a nutrition program and all its associated meals.
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # Delete meals
    cur.execute(
        "DELETE FROM nutrition_meals WHERE nutrition_program_id = %s",
        (program_id,),
    )

    # Delete program
    cur.execute(
        "DELETE FROM nutrition_programs WHERE id = %s",
        (program_id,),
    )

    db.commit()
    return {"ok": True}


# --------------------------------------------------
# STUDENTS FILTERS
# --------------------------------------------------
@router.get("/students/new-programs")
def get_students_with_new_programs(
    days: int = Query(7, ge=1, le=365),
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor()

    cur.execute(
        """
        WITH latest_workout AS (
            SELECT client_user_id, MAX(created_at) AS last_workout_at
            FROM workout_programs
            WHERE coach_user_id = %s
            GROUP BY client_user_id
        ),
        latest_nutrition AS (
            SELECT client_user_id, MAX(created_at) AS last_nutrition_at
            FROM nutrition_programs
            WHERE coach_user_id = %s
            GROUP BY client_user_id
        )
        SELECT
            u.id AS student_id,
            u.email,
            COALESCE(o.full_name, u.email) AS full_name,
            c.goal_type,
            c.activity_level,
            c.onboarding_done,
            c.created_at,
            lw.last_workout_at,
            ln.last_nutrition_at,
            GREATEST(
                COALESCE(lw.last_workout_at, '1970-01-01'::timestamp),
                COALESCE(ln.last_nutrition_at, '1970-01-01'::timestamp)
            ) AS last_program_at
        FROM clients c
        JOIN users u ON u.id = c.user_id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        LEFT JOIN latest_workout lw ON lw.client_user_id = u.id
        LEFT JOIN latest_nutrition ln ON ln.client_user_id = u.id
        WHERE c.assigned_coach_id = %s
          AND GREATEST(
                COALESCE(lw.last_workout_at, '1970-01-01'::timestamp),
                COALESCE(ln.last_nutrition_at, '1970-01-01'::timestamp)
          ) >= NOW() - (%s || ' days')::interval
        ORDER BY last_program_at DESC NULLS LAST, u.id DESC;
        """,
        (coach_id, coach_id, coach_id, days),
    )
    return {"students": cur.fetchall()}


@router.get("/students/all")
def get_all_students_from_subscriptions(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        WITH latest AS (
            SELECT DISTINCT ON (s.client_user_id)
                s.client_user_id,
                s.coach_user_id,
                s.status,
                s.started_at,
                s.ends_at,
                s.created_at AS purchased_at
            FROM subscriptions s
            WHERE s.coach_user_id = %s
            ORDER BY s.client_user_id, s.created_at DESC
        )
        SELECT
            u.id AS student_id,
            u.email,
            u.profile_photo_url,
            COALESCE(o.full_name, u.email) AS full_name,
            c.goal_type,
            l.status,
            l.started_at,
            l.ends_at,
            l.purchased_at,
            CASE
                WHEN l.status = 'active' AND l.ends_at > NOW() THEN TRUE
                ELSE FALSE
            END AS is_active
        FROM latest l
        JOIN users u ON u.id = l.client_user_id
        LEFT JOIN clients c ON c.user_id = u.id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        ORDER BY l.purchased_at DESC;
        """,
        (coach_id,),
    )
    return {"students": cur.fetchall()}


@router.get("/students/active")
def get_active_students_from_subscriptions(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT DISTINCT
            u.id AS student_id,
            u.email,
            u.profile_photo_url,
            COALESCE(o.full_name, u.email) AS full_name,
            c.goal_type,
            s.ends_at,
            EXTRACT(DAY FROM s.ends_at - NOW())::int AS days_left
        FROM subscriptions s
        JOIN users u ON u.id = s.client_user_id
        LEFT JOIN clients c ON c.user_id = u.id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        WHERE s.coach_user_id = %s
          AND s.status = 'active'
          AND s.ends_at > NOW()
        ORDER BY s.ends_at ASC
        """,
        (coach_id,),
    )
    return {"students": cur.fetchall()}



# --------------------------------------------------
# COACH PROFILE (ME)
# --------------------------------------------------
@router.get("/me/profile")
def get_my_profile(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT c.user_id, c.bio, c.photo_url, c.price_per_month, c.rating, c.rating_count,
               c.specialties, c.instagram, c.twitter, c.linkedin, c.website, c.is_active, c.title, c.certificates, c.photos,
               u.email, COALESCE(u.full_name, u.email) AS full_name
        FROM coaches c
        JOIN users u ON u.id = c.user_id
        WHERE c.user_id = %s
        """,
        (coach_id,),
    )
    row = cur.fetchone()

    if not row:
        cur.execute(
            """
            INSERT INTO coaches (user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active)
            VALUES (%s, '', NULL, NULL, 0, 0, ARRAY[]::text[], NULL, TRUE)
            RETURNING user_id, bio, photo_url, price_per_month, rating, rating_count, specialties, instagram, is_active
            """,
            (coach_id,),
        )
        row = cur.fetchone()
        db.commit()
        # Add user info to the new row
        cur.execute("SELECT email, COALESCE(full_name, email) AS full_name FROM users WHERE id = %s", (coach_id,))
        user_row = cur.fetchone()
        if user_row:
            row = dict(row)
            row["email"] = user_row["email"]
            row["full_name"] = user_row["full_name"]

    return {"profile": row}


@router.put("/me/profile")
def update_my_profile(
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Update users table fields (full_name, email)
    user_updates = []
    user_values = []
    if payload.get("full_name") is not None:
        user_updates.append("full_name = %s")
        user_values.append(payload["full_name"].strip() or None)
    if payload.get("email") is not None:
        user_updates.append("email = %s")
        user_values.append(payload["email"].strip() or None)
    if user_updates:
        user_values.append(coach_id)
        cur.execute(
            f"UPDATE users SET {', '.join(user_updates)} WHERE id = %s",
            tuple(user_values),
        )

    # Update coaches table fields
    allowed_fields = {"bio", "photo_url", "price_per_month", "specialties", "instagram", "twitter", "linkedin", "website", "is_active", "title", "certificates", "photos"}
    updates = {k: payload.get(k) for k in payload.keys() if k in allowed_fields}

    if updates:
        set_parts = []
        values = []
        for k, v in updates.items():
            set_parts.append(f"{k}=%s")
            values.append(v)

        values.append(coach_id)

        cur.execute(
            f"""
            UPDATE coaches
            SET {", ".join(set_parts)}
            WHERE user_id = %s
            """,
            tuple(values),
        )

    # Return full profile with user info
    cur.execute(
        """
        SELECT c.user_id, c.bio, c.photo_url, c.price_per_month, c.rating, c.rating_count,
               c.specialties, c.instagram, c.twitter, c.linkedin, c.website, c.is_active, c.title, c.certificates, c.photos,
               u.email, COALESCE(u.full_name, u.email) AS full_name
        FROM coaches c
        JOIN users u ON u.id = c.user_id
        WHERE c.user_id = %s
        """,
        (coach_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Coach profile not found")

    db.commit()
    return {"ok": True, "profile": row}


# --------------------------------------------------
# PACKAGES (NEW)
# --------------------------------------------------
def validate_services(services: Optional[List[str]]) -> List[str]:
    """
    Validate and normalize services list.
    - If None, return empty list
    - Max 12 tags
    - Each tag max 40 chars, trimmed
    """
    if services is None:
        return []
    
    # Trim and filter empty strings
    normalized = [s.strip() for s in services if s and s.strip()]
    
    # Max 12 tags
    if len(normalized) > 12:
        raise ValueError("Maximum 12 service tags allowed")
    
    # Each tag max 40 chars
    for tag in normalized:
        if len(tag) > 40:
            raise ValueError(f"Service tag '{tag}' exceeds 40 characters")
    
    return normalized


class CoachPackageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    duration_days: int = Field(gt=0)
    price: float = Field(ge=0)
    discount_percentage: float = Field(default=0, ge=0, le=100)
    is_active: bool = True
    services: Optional[List[str]] = Field(default=None, description="List of service tags (max 12, each max 40 chars)")
    image_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator('services')
    @classmethod
    def validate_services_field(cls, v):
        return validate_services(v)


class CoachPackageUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    duration_days: Optional[int] = Field(default=None, gt=0)
    price: Optional[float] = Field(default=None, ge=0)
    discount_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    services: Optional[List[str]] = Field(default=None, description="List of service tags (max 12, each max 40 chars)")
    image_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator('services')
    @classmethod
    def validate_services_field(cls, v):
        return validate_services(v)


@router.get("/packages")
def list_my_packages(db=Depends(get_db), current_user=Depends(require_role("coach"))):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            SELECT id, coach_user_id, name, description, duration_days, price, discount_percentage, is_active, services, image_url, created_at, updated_at
            FROM coach_packages
            WHERE coach_user_id = %s
            ORDER BY is_active DESC, created_at DESC, id DESC
            """,
            (current_user["id"],),
        )
        return {"packages": cur.fetchall()}
    except psycopg2.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error in /coach/packages: {e.pgerror or str(e)}")


@router.post("/packages")
def create_package(body: CoachPackageCreate, db=Depends(get_db), current_user=Depends(require_role("coach"))):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            INSERT INTO coach_packages (coach_user_id, name, description, duration_days, price, discount_percentage, is_active, services, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, coach_user_id, name, description, duration_days, price, discount_percentage, is_active, services, image_url, created_at, updated_at
            """,
            (current_user["id"], body.name, body.description, body.duration_days, body.price, body.discount_percentage, body.is_active, body.services, body.image_url),
        )
        row = cur.fetchone()
        db.commit()
        return {"package": row}
    except psycopg2.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error in POST /coach/packages: {e.pgerror or str(e)}")


@router.put("/packages/{package_id}")
def update_package(package_id: int, body: CoachPackageUpdate, db=Depends(get_db), current_user=Depends(require_role("coach"))):
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT id FROM coach_packages WHERE id=%s AND coach_user_id=%s",
            (package_id, current_user["id"]),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Package not found")

        fields = []
        values = []

        if body.name is not None:
            fields.append("name=%s"); values.append(body.name)
        if body.description is not None:
            fields.append("description=%s"); values.append(body.description)
        if body.duration_days is not None:
            fields.append("duration_days=%s"); values.append(body.duration_days)
        if body.price is not None:
            fields.append("price=%s"); values.append(body.price)
        if body.is_active is not None:
            fields.append("is_active=%s"); values.append(body.is_active)
        if body.discount_percentage is not None:
            fields.append("discount_percentage=%s"); values.append(body.discount_percentage)
        if body.services is not None:
            fields.append("services=%s"); values.append(body.services)
        if body.image_url is not None:
            fields.append("image_url=%s"); values.append(body.image_url)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        values.extend([package_id, current_user["id"]])

        cur.execute(
            f"""
            UPDATE coach_packages
            SET {", ".join(fields)}
            WHERE id=%s AND coach_user_id=%s
            RETURNING id, coach_user_id, name, description, duration_days, price, discount_percentage, is_active, services, image_url, created_at, updated_at
            """,
            tuple(values),
        )
        row = cur.fetchone()
        db.commit()
        return {"package": row}
    except HTTPException:
        raise
    except psycopg2.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error in PUT /coach/packages: {e.pgerror or str(e)}")


# --------------------------------------------------
# DASHBOARD SUMMARY
# --------------------------------------------------
@router.get("/dashboard/summary")
def get_dashboard_summary(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # 1) Unread messages count
    cur.execute("""
        SELECT COUNT(*)::int AS total_unread
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE c.coach_user_id = %s
          AND m.sender_type = 'client'
          AND m.read_at IS NULL
    """, (coach_id,))
    unread_messages = cur.fetchone()["total_unread"]

    # 2) Pending approvals count
    cur.execute("""
        SELECT COUNT(*)::int AS cnt
        FROM subscriptions
        WHERE coach_user_id = %s
          AND status = 'pending'
          AND purchased_at >= NOW() - INTERVAL '7 days'
    """, (coach_id,))
    pending_approvals = cur.fetchone()["cnt"]

    # 3) Active students count
    cur.execute("""
        SELECT COUNT(*)::int AS cnt
        FROM clients
        WHERE assigned_coach_id = %s
    """, (coach_id,))
    active_students = cur.fetchone()["cnt"]

    # 4) Ending soon: active subscriptions ending within 7 days
    cur.execute("""
        SELECT
            u.id AS student_id,
            COALESCE(o.full_name, u.email) AS full_name,
            u.profile_photo_url,
            s.ends_at,
            EXTRACT(DAY FROM s.ends_at - NOW())::int AS days_left
        FROM subscriptions s
        JOIN users u ON u.id = s.client_user_id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        WHERE s.coach_user_id = %s
          AND s.status = 'active'
          AND s.ends_at > NOW()
          AND s.ends_at <= NOW() + INTERVAL '7 days'
        ORDER BY s.ends_at ASC
    """, (coach_id,))
    ending_soon = cur.fetchall()

    # 5) Onboarding incomplete
    cur.execute("""
        SELECT
            u.id AS student_id,
            COALESCE(o.full_name, u.email) AS full_name,
            u.profile_photo_url
        FROM clients c
        JOIN users u ON u.id = c.user_id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        WHERE c.assigned_coach_id = %s
          AND (c.onboarding_done IS NULL OR c.onboarding_done = FALSE)
        ORDER BY u.id
    """, (coach_id,))
    onboarding_incomplete = cur.fetchall()

    # 6) Monthly revenue (from active subscriptions via coach_packages price)
    cur.execute("""
        SELECT COALESCE(SUM(cp.price), 0)::int AS monthly_revenue
        FROM subscriptions s
        JOIN coach_packages cp ON cp.id = s.package_id
        WHERE s.coach_user_id = %s
          AND s.status = 'active'
          AND s.ends_at > NOW()
    """, (coach_id,))
    monthly_revenue = cur.fetchone()["monthly_revenue"]

    # 7) Students without active workout program
    cur.execute("""
        SELECT
            u.id AS student_id,
            COALESCE(o.full_name, u.email) AS full_name,
            u.profile_photo_url,
            'workout' AS missing_type
        FROM clients c
        JOIN users u ON u.id = c.user_id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        WHERE c.assigned_coach_id = %s
          AND NOT EXISTS (
              SELECT 1 FROM workout_programs wp
              WHERE wp.client_user_id = u.id
                AND wp.coach_user_id = %s
                AND wp.is_active = TRUE
          )
        ORDER BY u.id
    """, (coach_id, coach_id))
    missing_workout = cur.fetchall()

    # 8) Students without active nutrition program
    cur.execute("""
        SELECT
            u.id AS student_id,
            COALESCE(o.full_name, u.email) AS full_name,
            u.profile_photo_url,
            'nutrition' AS missing_type
        FROM clients c
        JOIN users u ON u.id = c.user_id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        WHERE c.assigned_coach_id = %s
          AND NOT EXISTS (
              SELECT 1 FROM nutrition_programs np
              WHERE np.client_user_id = u.id
                AND np.coach_user_id = %s
                AND np.is_active = TRUE
          )
        ORDER BY u.id
    """, (coach_id, coach_id))
    missing_nutrition = cur.fetchall()

    # 9) Coach name for greeting
    cur.execute("""
        SELECT COALESCE(u.full_name, u.email) AS coach_name
        FROM users u
        WHERE u.id = %s
    """, (coach_id,))
    coach_row = cur.fetchone()
    coach_name = coach_row["coach_name"] if coach_row else ""

    # 10) Recent activity: last 10 events
    cur.execute("""
        (
            SELECT
                'new_message' AS event_type,
                m.created_at AS event_at,
                COALESCE(o.full_name, u.email) AS actor_name,
                CASE WHEN m.message_type = 'image' THEN '[Photo]'
                     ELSE LEFT(m.body, 80)
                END AS detail
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.client_user_id
            LEFT JOIN client_onboarding o ON o.user_id = u.id
            WHERE c.coach_user_id = %s
              AND m.sender_type = 'client'
            ORDER BY m.created_at DESC
            LIMIT 10
        )
        UNION ALL
        (
            SELECT
                'subscription_approved' AS event_type,
                s.decided_at AS event_at,
                COALESCE(o.full_name, u.email) AS actor_name,
                s.plan_name AS detail
            FROM subscriptions s
            JOIN users u ON u.id = s.client_user_id
            LEFT JOIN client_onboarding o ON o.user_id = u.id
            WHERE s.coach_user_id = %s
              AND s.decision = 'approved'
              AND s.decided_at IS NOT NULL
            ORDER BY s.decided_at DESC
            LIMIT 10
        )
        UNION ALL
        (
            SELECT
                'new_purchase' AS event_type,
                s.purchased_at AS event_at,
                COALESCE(o.full_name, u.email) AS actor_name,
                s.plan_name AS detail
            FROM subscriptions s
            JOIN users u ON u.id = s.client_user_id
            LEFT JOIN client_onboarding o ON o.user_id = u.id
            WHERE s.coach_user_id = %s
              AND s.status = 'pending'
            ORDER BY s.purchased_at DESC
            LIMIT 10
        )
        UNION ALL
        (
            SELECT
                'program_assigned' AS event_type,
                wp.updated_at AS event_at,
                COALESCE(o.full_name, u.email) AS actor_name,
                wp.title AS detail
            FROM workout_programs wp
            JOIN users u ON u.id = wp.client_user_id
            LEFT JOIN client_onboarding o ON o.user_id = u.id
            WHERE wp.coach_user_id = %s
              AND wp.is_active = TRUE
            ORDER BY wp.updated_at DESC
            LIMIT 10
        )
        ORDER BY event_at DESC NULLS LAST
        LIMIT 10
    """, (coach_id, coach_id, coach_id, coach_id))
    recent_activity = cur.fetchall()

    # Recent purchases (all statuses, last 30 days)
    cur.execute("""
        SELECT
            s.id AS subscription_id,
            s.client_user_id AS student_id,
            COALESCE(o.full_name, u.full_name, u.email) AS student_name,
            u.profile_photo_url AS student_photo,
            s.plan_name,
            s.status,
            s.purchased_at
        FROM subscriptions s
        JOIN users u ON u.id = s.client_user_id
        LEFT JOIN client_onboarding o ON o.user_id = u.id
        WHERE s.coach_user_id = %s
          AND s.purchased_at >= NOW() - INTERVAL '30 days'
        ORDER BY s.purchased_at DESC
        LIMIT 20
    """, (coach_id,))
    recent_purchases = cur.fetchall()

    # Serialize datetimes
    for item in recent_activity:
        if item.get("event_at") and hasattr(item["event_at"], "isoformat"):
            item["event_at"] = item["event_at"].isoformat()
    for item in ending_soon:
        if item.get("ends_at") and hasattr(item["ends_at"], "isoformat"):
            item["ends_at"] = item["ends_at"].isoformat()
    for item in recent_purchases:
        if item.get("purchased_at") and hasattr(item["purchased_at"], "isoformat"):
            item["purchased_at"] = item["purchased_at"].isoformat()

    return {
        "coach_name": coach_name,
        "kpi": {
            "unread_messages": unread_messages,
            "pending_approvals": pending_approvals,
            "active_students": active_students,
            "ending_soon_count": len(ending_soon),
            "monthly_revenue": monthly_revenue,
        },
        "needed": {
            "ending_soon": ending_soon,
            "onboarding_incomplete": onboarding_incomplete,
            "missing_workout": missing_workout,
            "missing_nutrition": missing_nutrition,
        },
        "recent_activity": recent_activity,
        "recent_purchases": recent_purchases,
    }


# --------------------------------------------------
# CARDIO PROGRAM SAVE (DRAFT)
# --------------------------------------------------
@router.post("/students/{student_user_id}/cardio-programs")
def save_cardio_program(
    student_user_id: int,
    payload: dict,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    try:
        # Create program as DRAFT (is_active=FALSE)
        cur.execute(
            """
            INSERT INTO cardio_programs (client_user_id, coach_user_id, title, is_active)
            VALUES (%s, %s, %s, FALSE)
            RETURNING id
            """,
            (student_user_id, coach_id, "Coach Cardio Program"),
        )
        program_id = _fetchone_id(cur.fetchone())

        sessions = payload.get("sessions", []) or []
        for idx, session in enumerate(sessions, start=1):
            if not isinstance(session, dict):
                continue
            cur.execute(
                """
                INSERT INTO cardio_sessions
                (cardio_program_id, day_of_week, cardio_type, duration_min, notes, order_index)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    program_id,
                    session.get("day_of_week") or "",
                    session.get("cardio_type") or "",
                    session.get("duration_min"),
                    session.get("notes") or "",
                    idx,
                ),
            )

        db.commit()
        return {"program_id": program_id, "message": "Kardiyo programı kaydedildi"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


@router.get("/students/{student_user_id}/cardio-programs/latest")
def get_latest_cardio_program(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Get the latest cardio program for a student (draft or active).
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    # Get latest cardio program
    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, title, is_active, created_at, updated_at
        FROM cardio_programs
        WHERE client_user_id=%s
        ORDER BY id DESC
        LIMIT 1
        """,
        (student_user_id,),
    )
    program = cur.fetchone()

    if not program:
        return {"program_id": None, "sessions": []}

    program_id = program["id"]

    # Get sessions for this program
    cur.execute(
        """
        SELECT id, cardio_program_id, day_of_week, cardio_type, duration_min, notes, order_index, created_at
        FROM cardio_sessions
        WHERE cardio_program_id=%s
        ORDER BY order_index ASC, id ASC
        """,
        (program_id,),
    )
    sessions = cur.fetchall() or []

    return {
        "program_id": program_id,
        "is_active": bool(program["is_active"]),
        "sessions": sessions,
    }


@router.post("/students/{student_user_id}/cardio-programs/assign")
def assign_latest_cardio_program(
    student_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Activate the latest cardio program for a student.
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    try:
        # Find latest cardio program for this student
        cur.execute(
            """
            SELECT id FROM cardio_programs
            WHERE client_user_id=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (student_user_id,),
        )
        program = cur.fetchone()

        if not program:
            raise HTTPException(status_code=404, detail="Cardio program not found")

        program_id = program["id"]

        # Deactivate all cardio programs for this student
        cur.execute(
            """
            UPDATE cardio_programs
            SET is_active = FALSE, updated_at = NOW()
            WHERE client_user_id = %s AND is_active = TRUE
            """,
            (student_user_id,),
        )

        # Activate the latest one
        cur.execute(
            """
            UPDATE cardio_programs
            SET is_active = TRUE, updated_at = NOW()
            WHERE id = %s
            """,
            (program_id,),
        )

        db.commit()
        return {"message": "Kardiyo programı atandı"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


@router.delete("/students/{student_user_id}/cardio-programs/{program_id}")
def delete_cardio_program(
    student_user_id: int,
    program_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """
    Delete a cardio program (sessions cascade via FK).
    """
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Verify student is assigned to this coach
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_user_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Student not assigned to this coach")

    cur.execute(
        """
        DELETE FROM cardio_programs
        WHERE id=%s AND client_user_id=(SELECT user_id FROM clients WHERE user_id=%s)
        """,
        (program_id, student_user_id),
    )

    db.commit()
    return {"message": "Kardiyo programı silindi"}


# ── Import sub-modules to register their routes on this router ──
try:
    from . import meal_photos  # noqa: F401
except Exception:
    pass
try:
    from . import drafts  # noqa: F401
except Exception:
    pass