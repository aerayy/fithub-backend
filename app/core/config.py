# app/core/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or ""
if not JWT_SECRET:
    import warnings
    warnings.warn("JWT_SECRET is not set — using insecure fallback. Set JWT_SECRET env var in production!", stacklevel=2)
    JWT_SECRET = "dev-only-insecure-fallback-change-me"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

DB_NAME = os.getenv("DB_NAME", "fithub")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
print("OPENAI_API_KEY loaded:", bool(OPENAI_API_KEY))