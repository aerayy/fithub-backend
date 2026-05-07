# app/api/health.py
import asyncio
import logging
import time
from fastapi import APIRouter

from app.core.config import OPENAI_API_KEY

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/_openai_ping")
async def openai_ping(model: str = "gpt-4.1-mini", timeout_s: float = 25.0):
    """Minimal OpenAI roundtrip test — Render→OpenAI baglantisinin sagligini olcer.
    Kullanici ekranindan curl ile cagrilir; auth gerekmez (gecici diagnostic)."""
    if not OPENAI_API_KEY:
        return {"ok": False, "error": "OPENAI_API_KEY not configured"}

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=timeout_s, max_retries=0)
    t0 = time.monotonic()
    try:
        async def _call():
            return await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
                max_tokens=5,
                temperature=0.0,
            )
        response = await asyncio.wait_for(_call(), timeout=timeout_s)
        dur = time.monotonic() - t0
        content = (response.choices[0].message.content or "").strip() if response.choices else ""
        logger.warning("openai_ping ok model=%s dur=%.2fs reply=%r", model, dur, content)
        return {"ok": True, "model": model, "duration_s": round(dur, 2), "reply": content}
    except asyncio.TimeoutError:
        dur = time.monotonic() - t0
        logger.error("openai_ping timeout model=%s after=%.2fs", model, dur)
        return {"ok": False, "model": model, "error": f"asyncio_timeout after {dur:.1f}s"}
    except Exception as e:
        dur = time.monotonic() - t0
        logger.exception("openai_ping error model=%s after=%.2fs", model, dur)
        return {"ok": False, "model": model, "error": f"{type(e).__name__}: {str(e)[:200]}", "duration_s": round(dur, 2)}
