# app/api/auth.py
import logging
import os
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Body
import bcrypt
from fastapi.security import OAuth2PasswordRequestForm
import psycopg2
import requests as _http
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt as jose_jwt
from jose.exceptions import JWTError, ExpiredSignatureError

from app.core.database import get_db
from app.core.security import create_token
from app.schemas.auth import SignUpRequest, LoginRequest, GoogleAuthRequest

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# Apple Sign-In configuration
# Bundle ID (iOS app's identifier) — required for audience check.
# Comma-separated list desteklenir (örn: bundle ID + service ID web Sign-in için).
APPLE_BUNDLE_IDS = [
    s.strip() for s in os.getenv("APPLE_BUNDLE_IDS", "com.fithubpoint.app").split(",") if s.strip()
]
APPLE_ISSUER = "https://appleid.apple.com"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"

# In-process cache for Apple JWKS keys (refreshed every hour)
_apple_keys_cache = {"keys": None, "expires_at": 0.0}

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup(req: SignUpRequest, db=Depends(get_db)):
    cur = db.cursor()
    
    # Store original autocommit setting
    original_autocommit = db.autocommit
    
    try:
        # Ensure we're in transaction mode
        db.autocommit = False
        
        cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()

        # ✅ Flutter client app: role backend tarafından otomatik "client"
        role = "client"

        print(f"[SIGNUP] Creating user with email={req.email}, role={role}")
        
        cur.execute(
            """
            INSERT INTO users (email, password_hash, full_name, timezone, phone_number, role, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id, email, full_name, role
            """,
            (req.email, hashed, None, "Europe/Istanbul", req.phone, role),
        )

        user = cur.fetchone()
        if not user:
            db.rollback()
            print(f"[SIGNUP] ERROR: User insert returned no row!")
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        user_id = user["id"]
        user_role = user["role"]
        
        print(f"[SIGNUP] User created successfully: user_id={user_id}, role={user_role}")

        # Insert into clients table only if role is 'client'
        if user_role == "client":
            print(f"[SIGNUP] Role is 'client', inserting into clients table for user_id={user_id}")
            cur.execute(
                """
                INSERT INTO clients (user_id, onboarding_done)
                VALUES (%s, FALSE)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (user_id,),
            )
            
            rows_affected = cur.rowcount
            if rows_affected > 0:
                print(f"[SIGNUP] Successfully inserted clients row for user_id={user_id}, rows_affected={rows_affected}")
            else:
                print(f"[SIGNUP] clients row already exists for user_id={user_id} (ON CONFLICT), rows_affected={rows_affected}")
        else:
            print(f"[SIGNUP] Role is '{user_role}', skipping clients table insert")

        # Commit both inserts (users + clients if applicable)
        print(f"[SIGNUP] Committing transaction...")
        db.commit()
        print(f"[SIGNUP] Transaction committed successfully")

        token = create_token(user["id"])
        return {"token": token, "user": user}
        
    except HTTPException:
        # Re-raise HTTP exceptions after rollback
        db.rollback()
        print(f"[SIGNUP] HTTPException raised, rolled back transaction")
        raise
    except psycopg2.Error as e:
        # Database errors
        db.rollback()
        print(f"[SIGNUP] Database error: {type(e).__name__}: {e}")
        print(f"[SIGNUP] Rolled back transaction due to database error")
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")
    except Exception as e:
        # Any other unexpected errors
        db.rollback()
        print(f"[SIGNUP] Unexpected error: {type(e).__name__}: {e}")
        print(f"[SIGNUP] Rolled back transaction due to unexpected error")
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")
    finally:
        # Restore original autocommit setting
        db.autocommit = original_autocommit



# /login endpoint moved to auth_v2.py (single source, supports email + phone + remember_me)


@router.post("/google")
def google_auth(req: GoogleAuthRequest, db=Depends(get_db)):
    """
    Google sign-in/sign-up via id_token.
    Body: { "id_token": "<Google JWT from Flutter>" }
    Returns same format as login: access_token, token, user
    """
    if not req.id_token or not req.id_token.strip():
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        idinfo = id_token.verify_oauth2_token(
            req.id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        logger.warning(f"[GOOGLE_AUTH] Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.warning(f"[GOOGLE_AUTH] Unexpected error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    google_sub = idinfo.get("sub")
    email = idinfo.get("email")
    name = idinfo.get("name") or (
        f"{idinfo.get('given_name', '')} {idinfo.get('family_name', '')}".strip()
        or None
    )

    if not google_sub:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    cur = db.cursor()

    # Find existing user: by auth_provider+provider_user_id, or by email
    cur.execute(
        """
        SELECT id, email, full_name, role
        FROM users
        WHERE (auth_provider = 'google' AND provider_user_id = %s)
           OR (email = %s AND email IS NOT NULL)
        ORDER BY CASE WHEN auth_provider = 'google' THEN 0 ELSE 1 END
        LIMIT 1
        """,
        (google_sub, email or ""),
    )
    user_row = cur.fetchone()

    if user_row:
        user_id = user_row["id"]
        # Update Google link if user existed by email but had no provider
        cur.execute(
            """
            UPDATE users
            SET auth_provider = 'google', provider_user_id = %s, updated_at = NOW()
            WHERE id = %s AND (auth_provider IS NULL OR auth_provider != 'google')
            """,
            (google_sub, user_id),
        )
        db.commit()
        user = dict(user_row)
    else:
        # Create new user
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Google account must have email for sign-up",
            )
        cur.execute(
            """
            INSERT INTO users (email, password_hash, full_name, role, auth_provider, provider_user_id, created_at, updated_at)
            VALUES (%s, NULL, %s, 'client', 'google', %s, NOW(), NOW())
            RETURNING id, email, full_name, role
            """,
            (email, name, google_sub),
        )
        new_user = cur.fetchone()
        if not new_user:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create user")
        user_id = new_user["id"]
        cur.execute(
            """
            INSERT INTO clients (user_id, onboarding_done)
            VALUES (%s, FALSE)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id,),
        )
        db.commit()
        user = dict(new_user)

    token = create_token(user["id"])
    return {
        "access_token": token,
        "token": token,
        "user": {
            "id": user["id"],
            "email": user.get("email"),
            "full_name": user.get("full_name"),
            "role": user.get("role", "client"),
        },
    }


# ─── Apple Sign-In (Apple Review Guideline 4.8 — Google/Facebook varsa zorunlu) ───

def _fetch_apple_public_keys():
    """Apple JWKS endpoint'inden public key listesi (1 saat cache'li)."""
    if _apple_keys_cache["keys"] and time.time() < _apple_keys_cache["expires_at"]:
        return _apple_keys_cache["keys"]
    try:
        resp = _http.get(APPLE_KEYS_URL, timeout=10)
        resp.raise_for_status()
        keys = resp.json().get("keys", []) or []
        _apple_keys_cache["keys"] = keys
        _apple_keys_cache["expires_at"] = time.time() + 3600
        return keys
    except Exception as e:
        logger.warning(f"[APPLE_AUTH] JWKS fetch failed: {e}")
        raise HTTPException(status_code=503, detail="Apple ile dogrulama gecici olarak kullanilamiyor")


def _verify_apple_identity_token(identity_token: str) -> dict:
    """Apple identity_token JWT'sini Apple public key'leriyle dogrular.
    Issuer + audience + signature kontrolü yapar. Geçerli payload döndürür."""
    if not identity_token or not identity_token.strip():
        raise HTTPException(status_code=401, detail="Invalid credentials")
    try:
        header = jose_jwt.get_unverified_header(identity_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    kid = header.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    keys = _fetch_apple_public_keys()
    matching_key = next((k for k in keys if k.get("kid") == kid), None)
    if not matching_key:
        # Cache stale ise tek seferlik refresh dene
        _apple_keys_cache["expires_at"] = 0
        keys = _fetch_apple_public_keys()
        matching_key = next((k for k in keys if k.get("kid") == kid), None)
        if not matching_key:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        payload = jose_jwt.decode(
            identity_token,
            matching_key,
            algorithms=["RS256"],
            audience=APPLE_BUNDLE_IDS if len(APPLE_BUNDLE_IDS) > 1 else APPLE_BUNDLE_IDS[0],
            issuer=APPLE_ISSUER,
            options={"verify_at_hash": False},
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token suresi dolmus")
    except JWTError as e:
        logger.warning(f"[APPLE_AUTH] JWT verify failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return payload


@router.post("/apple")
def apple_auth(payload: dict = Body(...), db=Depends(get_db)):
    """Apple Sign-In: Flutter'dan gelen identity_token (JWT) Apple ile doğrulanır.
    Body: { "id_token": "<JWT>", "user": { "name": "...", "email": "..." } }
       Apple email ve isim yalnızca ilk girişte gelir, sonraki girişlerde
       Flutter `user` payload'unu boş gönderir.
    """
    identity_token = (payload.get("id_token") or "").strip()
    user_info = payload.get("user") or {}
    if not isinstance(user_info, dict):
        user_info = {}
    fallback_name = (user_info.get("name") or "").strip() or None
    fallback_email = (user_info.get("email") or "").strip() or None

    if not identity_token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    claims = _verify_apple_identity_token(identity_token)
    apple_sub = claims.get("sub")
    email = claims.get("email") or fallback_email
    email_verified = claims.get("email_verified")
    if isinstance(email_verified, str):
        email_verified = email_verified.lower() == "true"
    if not apple_sub:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    cur = db.cursor()

    # Find by Apple sub first, then by email
    cur.execute(
        """
        SELECT id, email, full_name, role
        FROM users
        WHERE (auth_provider = 'apple' AND provider_user_id = %s)
           OR (email = %s AND email IS NOT NULL)
        ORDER BY CASE WHEN auth_provider = 'apple' THEN 0 ELSE 1 END
        LIMIT 1
        """,
        (apple_sub, email or ""),
    )
    user_row = cur.fetchone()

    if user_row:
        user_id = user_row["id"]
        # Apple link'i yoksa ekle
        cur.execute(
            """
            UPDATE users
            SET auth_provider = 'apple',
                provider_user_id = %s,
                updated_at = NOW()
            WHERE id = %s AND (auth_provider IS NULL OR auth_provider != 'apple')
            """,
            (apple_sub, user_id),
        )
        db.commit()
        user = dict(user_row)
    else:
        if not email:
            # İlk Apple girişinde email genelde gelir; "Hide My Email" aktifse
            # @privaterelay.appleid.com formatında gelir, yine de gelir.
            # Email yoksa hesap oluşturamayız.
            raise HTTPException(
                status_code=400,
                detail="Apple hesabinda email bilgisi yok. Lütfen E-posta paylaşımına izin verin.",
            )
        cur.execute(
            """
            INSERT INTO users
                (email, password_hash, full_name, role,
                 auth_provider, provider_user_id, email_verified,
                 created_at, updated_at)
            VALUES (%s, NULL, %s, 'client', 'apple', %s, %s, NOW(), NOW())
            RETURNING id, email, full_name, role
            """,
            (email, fallback_name, apple_sub, bool(email_verified) if email_verified is not None else True),
        )
        new_user = cur.fetchone()
        if not new_user:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create user")
        user_id = new_user["id"]
        cur.execute(
            """
            INSERT INTO clients (user_id, onboarding_done)
            VALUES (%s, FALSE)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id,),
        )
        db.commit()
        user = dict(new_user)

    token = create_token(user["id"])
    return {
        "access_token": token,
        "token": token,
        "user": {
            "id": user["id"],
            "email": user.get("email"),
            "full_name": user.get("full_name"),
            "role": user.get("role", "client"),
        },
    }


@router.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """
    Swagger OAuth2PasswordBearer için standart endpoint.
    form_data.username = email
    form_data.password = password
    """
    cur = db.cursor()
    cur.execute(
        """
        SELECT id, email, full_name, password_hash
        FROM users
        WHERE email = %s
        """,
        (form_data.username,),
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(form_data.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_token(user["id"])
    return {"access_token": access_token, "token_type": "bearer"}

