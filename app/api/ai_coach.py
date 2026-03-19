"""AI Coach chat endpoint — proxies requests to Claude API."""
import os
import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.security import require_role

router = APIRouter(prefix="/ai-coach", tags=["ai-coach"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


class ChatRequest(BaseModel):
    message: str
    system_prompt: str = ""


@router.post("/chat")
def ai_coach_chat(
    body: ChatRequest,
    current_user=Depends(require_role("client")),
):
    """Proxy chat request to Claude API."""
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="AI Coach not configured")

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
            return {"response": text}
        else:
            return {"response": ""}

    except Exception as e:
        print(f"[AI Coach] Claude API error: {e}")
        return {"response": ""}
