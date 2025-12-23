# app/core/security.py
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError

from app.core.config import JWT_SECRET, JWT_ALGORITHM
from app.core.database import get_db

bearer_scheme = HTTPBearer()

def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),  # <- string yapıyoruz (standart)
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db=Depends(get_db),
):
    token = credentials.credentials
    payload = decode_token(token)

    user_id_raw = payload.get("sub")
    try:
        user_id = int(user_id_raw)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    cur = db.cursor()
    cur.execute("SELECT id, email, role FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_role(*roles: str):
    """
    Kullanım:
      Depends(require_role("coach"))
      Depends(require_role("client", "coach"))
    """
    def _dep(user=Depends(get_current_user)):
        if roles and user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return _dep

