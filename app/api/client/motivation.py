import json
import logging

from fastapi import Depends, HTTPException
from psycopg2.extras import RealDictCursor, Json

from app.core.database import get_db
from app.core.security import require_role
from app.core.config import OPENAI_API_KEY
from .routes import router

logger = logging.getLogger(__name__)


@router.get("/daily-motivation")
def get_daily_motivation(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    user_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Check cache (valid for today)
    cur.execute(
        """
        SELECT motivation_json, generated_at
        FROM client_motivation_cache
        WHERE user_id = %s AND generated_at::date = CURRENT_DATE
        """,
        (user_id,),
    )
    cached = cur.fetchone()
    if cached:
        return cached["motivation_json"]

    # Fetch client onboarding data
    cur.execute(
        """
        SELECT
            co.age, co.weight_kg, co.height_cm, co.gender, co.your_goal,
            co.experience, co.how_fit, co.knee_pain, co.stressed,
            co.body_part_focus, co.pref_workout_length, co.workout_place,
            co.bad_habit, co.full_name
        FROM client_onboarding co
        WHERE co.user_id = %s
        """,
        (user_id,),
    )
    client_data = cur.fetchone()

    if not client_data:
        raise HTTPException(status_code=404, detail="Client onboarding data not found")

    # Fetch coach name
    cur.execute(
        """
        SELECT u.full_name
        FROM clients c
        JOIN users u ON u.id = c.assigned_coach_id
        WHERE c.user_id = %s AND c.assigned_coach_id IS NOT NULL
        """,
        (user_id,),
    )
    coach_row = cur.fetchone()
    coach_name = coach_row["full_name"] if coach_row else "Koçun"

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        from openai import OpenAI
    except ImportError:
        raise HTTPException(status_code=500, detail="OpenAI library not installed")

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        client_name = client_data.get("full_name") or "Sporcu"
        goal = client_data.get("your_goal") or "genel fitness"
        experience = client_data.get("experience") or "başlangıç"
        fitness_level = client_data.get("how_fit") or "başlangıç"
        stress = client_data.get("stressed") or "bilinmiyor"
        knee_pain = client_data.get("knee_pain")

        injury_note = ""
        if knee_pain:
            injury_note = " Müşterinin diz ağrısı var, bunu dikkate al."

        prompt = f"""Bir fitness koçu olarak günlük motivasyon mesajı yaz.

Koç Adı: {coach_name}
Müşteri Adı: {client_name}
Müşteri Profili:
- Hedef: {goal}
- Deneyim: {experience}, Fitness seviyesi: {fitness_level}
- Stres seviyesi: {stress}
{injury_note}

Koçun ağzından, müşteriye özel kısa ve motive edici bir günlük mesaj yaz.
Mesaj samimi, enerjik ve kişiselleştirilmiş olmalı.
Müşterinin hedefine ve durumuna referans ver.

Return ONLY valid JSON (no markdown):
{{
  "coach_name": "{coach_name}",
  "message": "Motivasyon mesajı burada (2-3 cümle, Türkçe)",
  "emoji": "uygun bir emoji"
}}

Rules:
- Mesaj 2-3 cümle olmalı
- Müşterinin adını kullan
- Koçun samimi tonunda yaz
- Türkçe yaz
- Emoji sadece tek bir emoji olmalı (💪, 🔥, ⚡, 🏋️, 🎯 gibi)"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Sen deneyimli bir fitness koçusun. Müşterine günlük motivasyon mesajı yazıyorsun. Sadece JSON formatında yanıt ver. Türkçe yaz.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )

        result = json.loads(response.choices[0].message.content)

        if "message" not in result:
            raise ValueError("Invalid response structure")

        # Ensure coach_name is correct
        result["coach_name"] = coach_name

        # Cache the result
        cur.execute(
            """
            INSERT INTO client_motivation_cache (user_id, motivation_json, generated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET motivation_json = EXCLUDED.motivation_json, generated_at = NOW()
            """,
            (user_id, Json(result)),
        )
        db.commit()

        logger.info(f"Daily motivation generated for user_id={user_id}")
        return result

    except json.JSONDecodeError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Invalid AI response: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating motivation for user_id={user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating motivation: {str(e)}")
