"""Body form photo AI analyzer — BETA.

GPT-4o-mini vision ile vücut form fotoğraflarından (1-4 açı) genel fitness
gözlemi ve antrenman odak önerisi üretir.

GÜVENLİK SINIRI: Tıbbi teşhis, rahatsızlık iddiası, kilo/ölçü tahmini YOK —
prompt bunu açıkça yasaklar. Çıktı motivasyonel fitness geri bildirimi;
kullanıcı UI'da BETA olarak görmeli.

Kullanım:
    result = analyze_body_photos([url1, url2, ...])
    # result = {overall, observations, focus_suggestions, confidence, model, analyzed_at}
    # veya None (fail)
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"
TIMEOUT_SEC = 40

SYSTEM_PROMPT = """Sen deneyimli, nazik bir fitness koçusun. Kullanıcının vücut form fotoğraflarına (ön/arka/yan açılar) bakarak genel bir fitness değerlendirmesi yaparsın.

KESIN KURALLAR:
- Tıbbi teşhis, hastalık/rahatsızlık iddiası, postür bozukluğu tanısı KOYMA.
- Kilo, yağ oranı, ölçü tahmini VERME.
- Aşağılayıcı/olumsuz dil KULLANMA; motive edici ve saygılı ol.
- Fotoğraflar yetersizse (karanlık, kırpık, tek açı) dürüstçe belirt ve confidence'ı "low" yap.

Şu JSON yapısında dön:
{
  "overall": "1-2 cümlelik genel, motive edici değerlendirme (Türkçe)",
  "observations": ["3-5 kısa gözlem — kas grubu gelişimi, genel denge, duruş gibi nazik ifadeler"],
  "focus_suggestions": ["2-4 antrenman odak önerisi — hangi bölgelere/hareket tiplerine ağırlık verilebilir"],
  "confidence": "low" | "medium" | "high"
}"""


def analyze_body_photos(photo_urls: list[str]) -> Optional[dict]:
    """1-4 vücut form fotoğrafını analiz eder.

    Args:
        photo_urls: Cloudinary URL listesi (batch'teki açılar)

    Returns:
        Analiz dict'i veya None (fail durumunda)
    """
    if not OPENAI_API_KEY:
        logger.warning("[BODY_AI] OPENAI_API_KEY yok, analiz yapılamıyor")
        return None
    if not photo_urls:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        logger.error("[BODY_AI] openai paketi kurulu değil")
        return None

    content: list[dict] = [
        {"type": "text", "text": f"Bu {len(photo_urls)} vücut form fotoğrafını değerlendir."}
    ]
    for url in photo_urls[:4]:
        content.append(
            {"type": "image_url", "image_url": {"url": url, "detail": "low"}}
        )

    try:
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=TIMEOUT_SEC)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=500,
        )
        data = json.loads(response.choices[0].message.content)

        if "overall" not in data:
            logger.warning(f"[BODY_AI] Eksik alan: {data}")
            return None

        result = {
            "overall": str(data.get("overall", ""))[:600],
            "observations": [str(x)[:200] for x in (data.get("observations") or [])][:5],
            "focus_suggestions": [str(x)[:200] for x in (data.get("focus_suggestions") or [])][:4],
            "confidence": data.get("confidence", "medium"),
            "model": MODEL,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"[BODY_AI] Analiz başarılı, confidence={result['confidence']}")
        return result
    except Exception as e:
        logger.error(f"[BODY_AI] Analiz hatası: {e}", exc_info=True)
        return None
