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


@router.get("/_sentry_test")
def sentry_test(key: str = ""):
    """Sentry'ye intentional exception gönderir. ADMIN_API_KEY ile korumalı."""
    import os
    expected = os.getenv("ADMIN_API_KEY", "")
    if not expected or key != expected:
        return {"ok": False, "error": "unauthorized"}
    raise RuntimeError("sentry_test: intentional crash (ignore in dashboard)")


@router.get("/_fcm_status")
def fcm_status(key: str = ""):
    """FCM kurulum durumu raporu. ADMIN_API_KEY ile korumalı."""
    import os
    expected = os.getenv("ADMIN_API_KEY", "")
    if not expected or key != expected:
        return {"ok": False, "error": "unauthorized"}
    from app.services import push_notification as pn
    pn._init_firebase()
    status = {
        "firebase_sdk_available": pn._firebase_available,
        "firebase_initialized": pn._firebase_initialized,
        "service_account_env_set": bool(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")),
        "service_account_file_exists": os.path.exists(
            os.path.join(os.path.dirname(pn.__file__), "../../firebase-service-account.json")
        ),
    }
    return {"ok": True, "status": status}


@router.get("/_fcm_test")
def fcm_test(user_id: int = 0, key: str = ""):
    """Verilen user_id'nin tum FCM tokenlerine test push atar."""
    import os
    expected = os.getenv("ADMIN_API_KEY", "")
    if not expected or key != expected:
        return {"ok": False, "error": "unauthorized"}
    if not user_id:
        return {"ok": False, "error": "user_id required"}
    from app.services.push_notification import send_notification, _get_user_tokens
    tokens = _get_user_tokens(user_id)
    if not tokens:
        return {"ok": False, "error": f"no fcm tokens for user_id={user_id}"}
    send_notification(
        user_id=user_id,
        title="FitHub Test",
        body="Push notification calisiyor!",
        data={"type": "test"},
    )
    return {"ok": True, "user_id": user_id, "tokens_count": len(tokens)}


@router.get("/_send_test_email")
def send_test_email(to: str = "", key: str = ""):
    """Resend bağlantısını test eder. ADMIN_API_KEY ile korumalı."""
    import os
    expected = os.getenv("ADMIN_API_KEY", "")
    if not expected or key != expected:
        return {"ok": False, "error": "unauthorized"}
    if not to or "@" not in to:
        return {"ok": False, "error": "invalid_recipient"}
    from app.services.email_service import send_email, render_welcome_email
    result = send_email(
        to=to,
        subject="FitHub — Test E-postası",
        html=render_welcome_email("Test Kullanıcı"),
    )
    return {"ok": "error" not in result and not result.get("skipped"), "result": result}


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
