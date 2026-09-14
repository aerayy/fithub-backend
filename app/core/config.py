# app/core/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or ""
if not JWT_SECRET:
    if os.getenv("RENDER"):
        # Prod (Render) güvensiz varsayılanla ASLA açılmasın — fail-fast.
        # Render deploy'u başarısız sayar ve eski sürümü canlıda tutar.
        raise RuntimeError(
            "JWT_SECRET (veya JWT_SECRET_KEY) tanımlı değil; production güvensiz "
            "varsayılan anahtarla açılamaz. Render env'ine ekle."
        )
    import warnings
    warnings.warn("JWT_SECRET is not set — using insecure fallback (sadece lokal/CI).", stacklevel=2)
    JWT_SECRET = "dev-only-insecure-fallback-change-me"
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

DB_NAME = os.getenv("DB_NAME", "fithub")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
# Koç self-signup için isteğe bağlı davet kodu. Boşsa kayıt açık (yalnızca rate limit).
COACH_INVITE_CODE = os.getenv("COACH_INVITE_CODE", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
print("OPENAI_API_KEY loaded:", bool(OPENAI_API_KEY))