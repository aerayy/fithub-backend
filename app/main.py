# app/main.py
import logging
import os as _os_cfg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    force=True,
)

# ---------------------------------------------------------------
# Sentry — crash reporting + performance. Init ÖNCE gelmeli.
# DSN env'de yoksa init atlanır (lokal dev için zararsız).
# ---------------------------------------------------------------
_SENTRY_DSN = _os_cfg.getenv("SENTRY_DSN", "").strip()
if _SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    _SENSITIVE_KEYS = {
        "password", "hashed_password", "old_password", "new_password",
        "token", "access_token", "refresh_token", "jwt", "authorization",
        "secret", "api_key", "openai_api_key", "admin_api_key",
        "otp", "otp_code", "verification_code",
    }

    def _scrub(obj):
        """Recursively redact sensitive fields from dicts/lists."""
        if isinstance(obj, dict):
            return {
                k: ("[REDACTED]" if k.lower() in _SENSITIVE_KEYS else _scrub(v))
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_scrub(x) for x in obj]
        return obj

    def _before_send(event, hint):
        # request payload + extra fields temizle
        if "request" in event and isinstance(event["request"], dict):
            req = event["request"]
            if "data" in req:
                req["data"] = _scrub(req["data"])
            if "headers" in req and isinstance(req["headers"], dict):
                req["headers"] = _scrub(req["headers"])
        if "extra" in event:
            event["extra"] = _scrub(event["extra"])
        return event

    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        environment=_os_cfg.getenv("RENDER_SERVICE_NAME", "local"),
        release=_os_cfg.getenv("RENDER_GIT_COMMIT", "unknown")[:12],
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        send_default_pii=False,  # KVKK — IP, cookie, body otomatik toplanmasın
        traces_sample_rate=0.1,  # %10 performance trace (free tier quota dostu)
        profiles_sample_rate=0.0,  # Profiling kapalı (quota tasarrufu)
        before_send=_before_send,
    )
    logging.getLogger(__name__).info("Sentry initialized for %s", _os_cfg.getenv("RENDER_SERVICE_NAME", "local"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.onboarding import router as onboarding_router
from app.api.workouts import router as workouts_router
from app.api.nutrition import router as nutrition_router
from app.api.admin import router as admin_router
from app.api.coach.routes import router as coach_router
from app.api.client.routes import router as client_router
from app.api.subscriptions import router as subscriptions_router
import os
from app.api.exercises import router as exercises_router
from app.api.foods import router as foods_router
from app.api.upload import router as upload_router
from app.api.ws import router as ws_router
from app.api.ai_coach import router as ai_coach_router
from app.api.auth_v2 import router as auth_v2_router
from app.api.ai_coach_purchase import router as ai_coach_purchase_router
from app.api.ai_subscription import router as ai_subscription_router
from app.api.revenuecat_webhook import router as revenuecat_webhook_router
from app.api.coach.workout_v3 import router as workout_v3_router
from app.api.superadmin import router as superadmin_router


from app.core.database import close_pool

app = FastAPI()


@app.on_event("shutdown")
def shutdown_db_pool():
    close_pool()

# ✅ DEV MODE: Her origin'e izin ver (cookie yok -> allow_credentials=False şart)
import os
from fastapi.middleware.cors import CORSMiddleware

cors_origins = os.getenv("CORS_ORIGINS", "")
origins = [o.strip() for o in cors_origins.split(",") if o.strip()]

# Landing sayfası her zaman izinli — şifre sıfırlama formu (sifre-sifirla.html)
# backend'e cross-origin POST atıyor; Render CORS_ORIGINS env'ine bağımlı kalmasın.
for _always_allow in ("https://fithubpoint.com", "https://www.fithubpoint.com"):
    if _always_allow not in origins:
        origins.append(_always_allow)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(workouts_router)
app.include_router(nutrition_router)
app.include_router(admin_router)
app.include_router(coach_router)
app.include_router(client_router)
app.include_router(subscriptions_router)
app.include_router(exercises_router)
app.include_router(foods_router)
app.include_router(upload_router)
app.include_router(ws_router)
app.include_router(ai_coach_router)
app.include_router(ai_coach_purchase_router)
app.include_router(ai_subscription_router)
app.include_router(revenuecat_webhook_router)
app.include_router(workout_v3_router)
app.include_router(auth_v2_router)
app.include_router(superadmin_router)


@app.get("/_version")
def _version():
    return {
        "commit": _os_cfg.getenv("RENDER_GIT_COMMIT", "unknown")[:12],
        "service": _os_cfg.getenv("RENDER_SERVICE_NAME", "local"),
    }

