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


@router.get("/_openai_stream_test")
async def openai_stream_test(model: str = "gpt-4.1-mini", timeout_s: float = 110.0, max_tokens: int = 4000):
    """Nutrition senaryosuna yakin: stream=True + response_format=json_object + buyuk output.
    Gercek bottleneck'i simule eder, kullanici beklemeden test."""
    if not OPENAI_API_KEY:
        return {"ok": False, "error": "OPENAI_API_KEY not configured"}

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=timeout_s, max_retries=0)
    t0 = time.monotonic()
    first_at = None
    chunk_count = 0
    parts = []
    try:
        async def _call():
            nonlocal first_at, chunk_count
            stream = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "JSON formatinda yanit ver."},
                    {"role": "user", "content": "Turkiye'de yaygin 50 yemegin listesini JSON olarak ver. Yapı: {\"yemekler\": [{\"isim\": \"...\", \"kategori\": \"...\", \"kalori_100g\": N}, ...]}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
                max_tokens=max_tokens,
                stream=True,
                stream_options={"include_usage": True},
            )
            usage_local = None
            finish_local = None
            async for ch in stream:
                nonlocal_first = first_at
                if first_at is None:
                    first_at = time.monotonic()
                chunk_count += 1
                if ch.choices:
                    c = ch.choices[0]
                    if getattr(c, "delta", None) and getattr(c.delta, "content", None):
                        parts.append(c.delta.content)
                    if getattr(c, "finish_reason", None):
                        finish_local = c.finish_reason
                if getattr(ch, "usage", None):
                    usage_local = ch.usage
            return finish_local, usage_local

        finish_reason, usage = await asyncio.wait_for(_call(), timeout=timeout_s)
        dur = time.monotonic() - t0
        ttfb = (first_at - t0) if first_at else None
        content = "".join(parts)
        return {
            "ok": True,
            "model": model,
            "duration_s": round(dur, 2),
            "ttfb_s": round(ttfb, 2) if ttfb is not None else None,
            "chunks": chunk_count,
            "content_chars": len(content),
            "finish_reason": finish_reason,
            "usage": str(usage) if usage else None,
        }
    except asyncio.TimeoutError:
        dur = time.monotonic() - t0
        ttfb = (first_at - t0) if first_at else None
        return {
            "ok": False,
            "error": f"asyncio_timeout after {dur:.1f}s",
            "ttfb_s": round(ttfb, 2) if ttfb is not None else None,
            "chunks_received": chunk_count,
            "content_chars": len("".join(parts)),
        }
    except Exception as e:
        dur = time.monotonic() - t0
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}", "duration_s": round(dur, 2)}
