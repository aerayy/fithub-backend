# app/core/security.py
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError

from app.core.config import JWT_SECRET, JWT_ALGORITHM, ADMIN_API_KEY
from app.core.database import get_db
from fastapi import Header

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

def verify_admin_key(x_admin_key: str = Header(..., alias="X-Admin-Key")):
    """
    Admin API key verification dependency.
    Requires X-Admin-Key header to match ADMIN_API_KEY env var.
    Returns 401 if missing or invalid (never crashes).
    """
    if not ADMIN_API_KEY or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing admin key"
        )
    return True
