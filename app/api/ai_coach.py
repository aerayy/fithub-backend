"""AI Coach chat endpoint — proxies requests to Claude API."""
import os
import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.security import require_role
from app.core.database import get_db
from app.services import ai_subscription_service as ai_sub

router = APIRouter(prefix="/ai-coach", tags=["ai-coach"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


class ChatRequest(BaseModel):
    message: str
    system_prompt: str = ""


@router.post("/chat")
def ai_coach_chat(
    body: ChatRequest,
    current_user=Depends(require_role("client")),
    db=Depends(get_db),
):
    """Proxy chat request to Claude API. Tier-gated by ai_subscription_service."""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI Coach not configured")

    # Quota check — reject before paying API costs
    allowed, reason = ai_sub.check_quota(db, current_user["id"], "chat")
    if not allowed:
        # 402 Payment Required mantığı: tier yok → upgrade gerek;
        # limit dolmuş → tier yeterli ama bu ay bitmiş.
        detail = {
            "code": reason,
            "message": _quota_message_tr(reason, "chat"),
        }
        raise HTTPException(status_code=402, detail=detail)

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-5-20241022",
                "max_tokens": 500,
                "system": body.system_prompt or "Sen FithubPoint AI fitness kocusun. Turkce, kisa ve motive edici cevaplar ver.",
                "messages": [
                    {"role": "user", "content": body.message}
                ],
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            text = data.get("content", [{}])[0].get("text", "")
            # Quota'yı sadece basarili cagri sonrasinda yak
            ai_sub.increment_quota(db, current_user["id"], "chat")
            return {"response": text}
        else:
            return {"response": ""}

    except Exception as e:
        print(f"[AI Coach] Claude API error: {e}")
        return {"response": ""}


def _quota_message_tr(reason: str, feature: str) -> str:
    """User-facing Turkish error messages for quota refusal."""
    messages = {
        "no_subscription": "Fit AI Koç aboneliğin bulunmuyor. Paketleri inceleyebilirsin.",
        "tier_disallowed": "Bu özellik mevcut paketinde yer almıyor. Yükseltebilirsin.",
        "limit_reached": "Bu ayki kullanım hakkını doldurdun. Paketini yükseltebilirsin.",
    }
    return messages.get(reason, "AI Koç şu an kullanılamıyor.")
