# app/core/security.py
import logging
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError

from app.core.config import JWT_SECRET, JWT_ALGORITHM, ADMIN_API_KEY
from app.core.database import get_db
from fastapi import Header

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()

def create_token(user_id: int, expiry_days: int = 7) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=expiry_days),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Oturum süresi doldu, lütfen tekrar giriş yap.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Geçersiz oturum, lütfen tekrar giriş yap.")

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
        raise HTTPException(status_code=401, detail="Geçersiz oturum, lütfen tekrar giriş yap.")

    cur = db.cursor()
    cur.execute("SELECT id, email, role FROM users WHERE id = %s", (user_id,))
    user_row = cur.fetchone()
    if not user_row:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Convert RealDictRow to dict and ensure we have the required fields
    user = {
        "id": user_row["id"],
        "email": user_row["email"],
        "role": user_row["role"],
    }

    # Sentry user context — sadece user_id + role gönder (email PII, atlanır)
    try:
        import sentry_sdk
        sentry_sdk.set_user({"id": str(user["id"]), "role": user["role"]})
    except Exception:
        pass  # Sentry yoksa sessiz geç

    # Debug log
    logger.debug(f"get_current_user: user_id={user['id']}, role={user['role']}")

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


# ── Kalıcı oturum (refresh token) ─────────────────────────────────────
# Access token (JWT) kısa ömürlü; refresh token opak, users.remember_token'da
# sha256 hash'i tutulur, 30 gün kayan pencere. Login/register/sosyal girişte
# verilir, /auth/refresh ile yeni JWT alınır. Çıkışta sunucuda silinir.
import hashlib as _hashlib
import secrets as _secrets
from datetime import datetime as _dt, timedelta as _td

REFRESH_TOKEN_DAYS = 30


def issue_refresh_token(cur, user_id: int) -> str:
    """Yeni refresh token üretir, hash'ini users tablosuna yazar, ham değeri döndürür.
    Çağıran commit etmeli."""
    raw = _secrets.token_urlsafe(48)
    cur.execute(
        "UPDATE users SET remember_token = %s, remember_token_expires_at = %s WHERE id = %s",
        (_hashlib.sha256(raw.encode()).hexdigest(), _dt.utcnow() + _td(days=REFRESH_TOKEN_DAYS), user_id),
    )
    return raw


def refresh_token_hash(raw: str) -> str:
    return _hashlib.sha256(raw.encode()).hexdigest()
