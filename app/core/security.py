# app/core/security.py
from datetime import datetime, timedelta
import jwt
from .config import JWT_SECRET, JWT_ALGORITHM

def create_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
