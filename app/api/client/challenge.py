import json
import logging

from fastapi import Depends, HTTPException
from psycopg2.extras import RealDictCursor, Json

from app.core.database import get_db
from app.core.security import require_role
from app.core.config import OPENAI_API_KEY
from .routes import router

logger = logging.getLogger(__name__)


@router.get("/daily-challenge")
def get_daily_challenge(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    user_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Check cache (valid for today)
    cur.execute(
        """
        SELECT challenge_json, generated_at
        FROM client_challenge_cache
        WHERE user_id = %s AND generated_at::date = CURRENT_DATE
        """,
        (user_id,),
    )
    cached = cur.fetchone()
    if cached:
        return cached["challenge_json"]

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

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        from openai import OpenAI
    except ImportError:
        raise HTTPException(status_code=500, detail="OpenAI library not installed")

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        age = client_data.get("age") or "bilinmiyor"
        gender = client_data.get("gender") or "bilinmiyor"
        goal = client_data.get("your_goal") or "genel fitness"
        experience = client_data.get("experience") or "başlangıç"
        fitness_level = client_data.get("how_fit") or "başlangıç"
        knee_pain = client_data.get("knee_pain")
        workout_place = client_data.get("workout_place") or "ev"
        body_focus = client_data.get("body_part_focus")

        injury_note = ""
        if knee_pain:
            injury_note = " Kullanıcının diz ağrısı var — diz üzerinde baskı oluşturacak hareketlerden kaçın."

        body_focus_desc = ""
        if body_focus:
            if isinstance(body_focus, dict):
                body_focus_desc = f" Odak bölgeleri: {', '.join(str(v) for v in body_focus.values())}."
            elif isinstance(body_focus, list):
                body_focus_desc = f" Odak bölgeleri: {', '.join(str(v) for v in body_focus)}."

        prompt = f"""Bir fitness uygulaması için kişiselleştirilmiş günlük challenge oluştur.

Kullanıcı Profili:
- Yaş: {age}, Cinsiyet: {gender}
- Hedef: {goal}
- Deneyim: {experience}, Fitness seviyesi: {fitness_level}
- Antrenman yeri: {workout_place}
{injury_note}{body_focus_desc}

Return ONLY valid JSON (no markdown):
{{
  "title": "Günün Challenge'ı",
  "description": "Kısa ve net challenge açıklaması (1-2 cümle, Türkçe)",
  "difficulty": "Kolay|Orta|Zor",
  "estimated_minutes": 10,
  "emoji": "⚡"
}}

Rules:
- Challenge kullanıcının seviyesine uygun olmalı (başlangıç=kolay, ileri=zor)
- Antrenman yerine uygun olmalı (ev=ekipmansız, gym=ekipmanlı)
- Diz ağrısı varsa diz dostu hareketler seç
- Her gün farklı kas gruplarına odaklan
- Süre 5-20 dakika arası olmalı
- Türkçe yaz
- Emoji tek bir emoji olmalı"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Sen bir fitness challenge tasarımcısısın. Kişiye özel günlük egzersiz challenge'ları oluşturuyorsun. Sadece JSON formatında yanıt ver. Türkçe yaz.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )

        result = json.loads(response.choices[0].message.content)

        if "description" not in result:
            raise ValueError("Invalid response structure")

        # Cache the result
        cur.execute(
            """
            INSERT INTO client_challenge_cache (user_id, challenge_json, generated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET challenge_json = EXCLUDED.challenge_json, generated_at = NOW()
            """,
            (user_id, Json(result)),
        )
        db.commit()

        logger.info(f"Daily challenge generated for user_id={user_id}")
        return result

    except json.JSONDecodeError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Invalid AI response: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating challenge for user_id={user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating challenge: {str(e)}")
