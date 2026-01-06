# app/core/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_THIS_TO_A_RANDOM_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

DB_NAME = os.getenv("DB_NAME", "fithub")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Eray123!")  # sonra .env'ye alacağız
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
