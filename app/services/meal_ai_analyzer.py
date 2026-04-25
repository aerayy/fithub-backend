"""
Meal photo AI analyzer — BETA.

GPT-4o-mini vision API ile yemek fotoğrafından makro tahmini yapar.

Türk mutfağı için karışık yemekler (etli pilav, kebap, börek) zorlu —
çıktı ±%20-30 hata payı içerir. Kullanıcı UI'da BETA olarak görmeli,
koç ground truth, AI yardımcı.

Kullanım:
    result = analyze_meal_photo(photo_url, meal_label="Öğle Yemeği")
    # result = {calories, protein_g, carbs_g, fat_g, items, confidence, model, analyzed_at}
    # veya None (fail)
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"  # cost-efficient, decent quality
TIMEOUT_SEC = 30

SYSTEM_PROMPT = """Sen profesyonel bir beslenme uzmanısın. Yemek fotoğraflarına bakarak makro besin tahmini yaparsın.

Görevin: Fotoğraftaki tabağı analiz et ve şu JSON yapısında dön:
{
  "items": [
    {"name": "Yemek adı (Türkçe)", "estimated_g": 150}
  ],
  "calories": 520,
  "protein_g": 35,
  "carbs_g": 60,
  "fat_g": 18,
  "confidence": "low" | "medium" | "high"
}

Kurallar:
- Türkçe yemek isimleri kullan (örn: "Izgara tavuk göğsü", "Pilav", "Mevsim salatası")
- Porsiyon (gram) tahmini en önemli kısım — tabak boyutuna göre dikkatli ol
- Görünmeyen yağ/sos/şeker varsa kalori hesaplamasında düşünmeyi unutma
- Karışık tabakta (etli pilav, kebap) en az 2-3 ayrı item belirt
- confidence: tek besin + standart porsiyon = "high", karışık tabak = "medium",
  görüntüde net olmayan/abartılı poz = "low"
- Sadece JSON dön, başka açıklama yapma."""


def analyze_meal_photo(photo_url: str, meal_label: Optional[str] = None) -> Optional[dict]:
    """
    Yemek fotoğrafını analiz et, makro tahmini yap.

    Args:
        photo_url: Cloudinary'deki yemek fotoğrafı URL'i
        meal_label: "Kahvaltı", "Öğle Yemeği" gibi (prompt'a yardımcı, opsiyonel)

    Returns:
        Analiz dict'i veya None (fail durumunda)
    """
    if not OPENAI_API_KEY:
        logger.warning("[MEAL_AI] OPENAI_API_KEY yok, analiz yapılamıyor")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        logger.error("[MEAL_AI] openai paketi kurulu değil")
        return None

    user_msg = "Bu öğün fotoğrafını analiz et."
    if meal_label:
        user_msg = f"Bu '{meal_label}' fotoğrafını analiz et."

    try:
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=TIMEOUT_SEC)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_msg},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": photo_url,
                                "detail": "low",  # cost reduction — yemek için yeterli
                            },
                        },
                    ],
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=400,
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        # Validation — minimum gerekli alanlar
        if not all(k in data for k in ("calories", "protein_g", "carbs_g", "fat_g")):
            logger.warning(f"[MEAL_AI] Eksik alan: {data}")
            return None

        # Normalize
        result = {
            "calories": int(data.get("calories", 0)),
            "protein_g": int(data.get("protein_g", 0)),
            "carbs_g": int(data.get("carbs_g", 0)),
            "fat_g": int(data.get("fat_g", 0)),
            "items": data.get("items", []),
            "confidence": data.get("confidence", "medium"),
            "model": MODEL,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"[MEAL_AI] Analiz başarılı: {result['calories']} kcal, confidence={result['confidence']}")
        return result

    except Exception as e:
        logger.error(f"[MEAL_AI] Analiz hatası: {e}", exc_info=True)
        return None
