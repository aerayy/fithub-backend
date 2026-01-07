# app/main.py
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


app = FastAPI()

# ✅ DEV MODE: Her origin'e izin ver (cookie yok -> allow_credentials=False şart)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
