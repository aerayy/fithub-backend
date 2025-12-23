# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.workouts import router as workouts_router
from app.api.nutrition import router as nutrition_router


from app.core.config import CORS_ORIGINS
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.onboarding import router as onboarding_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(workouts_router)
app.include_router(nutrition_router)
