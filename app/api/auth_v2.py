"""Auth v2 — complete authentication flow with OTP, email verification, remember me."""
import os
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from typing import Optional
from psycopg2.extras import RealDictCursor
import bcrypt

from app.core.database import get_db
from app.core.security import create_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth-v2"])


# ─── Models ───

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    password_confirm: str
    birthdate: str  # YYYY-MM-DD

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Geçersiz e-posta formatı')
        return v.lower().strip()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        cleaned = re.sub(r'[^0-9]', '', v)
        if cleaned.startswith('90'):
            cleaned = cleaned[2:]
        if not cleaned.startswith('5') or len(cleaned) != 10:
            raise ValueError('Geçersiz telefon numarası. Örnek: 05xx xxx xx xx')
        return f'+90{cleaned}'

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Şifre en az 8 karakter olmalı')
        if not re.search(r'[0-9]', v):
            raise ValueError('Şifre en az 1 rakam içermeli')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Şifre en az 1 harf içermeli')
        return v


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str


class LoginRequest(BaseModel):
    identifier: str = ""  # email or phone
    email: str = ""  # Flutter compatibility (sends "email" instead of "identifier")
    password: str
    remember_me: bool = False


class ForgotPasswordRequest(BaseModel):
    method: str  # email or phone
    identifier: str


class ResetPasswordRequest(BaseModel):
    phone: Optional[str] = None
    otp: Optional[str] = None
    token: Optional[str] = None
    new_password: str


# ─── Helpers ───

def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def _generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def _normalize_phone(phone: str) -> str:
    cleaned = re.sub(r'[^0-9]', '', phone)
    if cleaned.startswith('90'):
        cleaned = cleaned[2:]
    if len(cleaned) == 10 and cleaned.startswith('5'):
        return f'+90{cleaned}'
    return phone


def _mask_phone(phone: str) -> str:
    if len(phone) >= 10:
        return f'{phone[:6]}***{phone[-2:]}'
    return phone


def _send_otp_sms(phone: str, otp: str):
    """Send OTP via SMS. TODO: integrate real SMS provider (Twilio/Netgsm)."""
    print(f'[SMS] OTP {otp} sent to {phone}')
    # In production: call Twilio/Netgsm API here


def _send_verification_email(email: str, token: str):
    """Send email verification link. TODO: integrate email provider."""
    link = f'https://fithub-backend-jd40.onrender.com/auth/verify-email/{token}'
    print(f'[EMAIL] Verification link sent to {email}: {link}')
    # In production: call SendGrid/SES API here


# ─── Endpoints ───

@router.post("/register")
def register(body: RegisterRequest, db=Depends(get_db)):
    """Register new user with OTP + email verification."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    # Password match
    if body.password != body.password_confirm:
        raise HTTPException(400, "Şifreler eşleşmiyor")

    # Age check
    try:
        birthdate = datetime.strptime(body.birthdate, '%Y-%m-%d').date()
        if birthdate > datetime.now().date():
            raise HTTPException(400, "Geçersiz doğum tarihi")
        age = (datetime.now().date() - birthdate).days // 365
        if age < 18:
            raise HTTPException(400, detail="AGE_RESTRICTION")
    except ValueError:
        raise HTTPException(400, "Doğum tarihi formatı: YYYY-MM-DD")

    # Check existing
    cur.execute("SELECT id FROM users WHERE email = %s", (body.email,))
    if cur.fetchone():
        raise HTTPException(400, "Bu e-posta zaten kayıtlı")

    cur.execute("SELECT id FROM users WHERE phone = %s", (body.phone,))
    if cur.fetchone():
        raise HTTPException(400, "Bu telefon numarası zaten kayıtlı")

    # Create user
    password_hash = _hash_password(body.password)
    otp = _generate_otp()
    otp_hash = _hash_otp(otp)
    email_token = secrets.token_urlsafe(48)

    cur.execute(
        """INSERT INTO users (email, phone, password_hash, full_name, role, birthdate,
           phone_verified, email_verified,
           otp_code, otp_expires_at, otp_attempts,
           email_verification_token, email_verification_expires_at,
           created_at)
           VALUES (%s, %s, %s, %s, 'client', %s,
           FALSE, FALSE,
           %s, %s, 0,
           %s, %s,
           NOW())
           RETURNING id""",
        (body.email, body.phone, password_hash, body.full_name, birthdate,
         otp_hash, datetime.utcnow() + timedelta(minutes=5),
         email_token, datetime.utcnow() + timedelta(hours=24)),
    )
    user_id = cur.fetchone()["id"]

    # Create client profile
    cur.execute(
        "INSERT INTO clients (user_id, onboarding_done, created_at) VALUES (%s, FALSE, NOW()) ON CONFLICT DO NOTHING",
        (user_id,),
    )

    db.commit()

    # Send OTP + email (async in production)
    _send_otp_sms(body.phone, otp)
    _send_verification_email(body.email, email_token)

    # Generate token for immediate use
    token = create_token(user_id)

    return {
        "ok": True,
        "user_id": user_id,
        "token": token,
        "masked_phone": _mask_phone(body.phone),
        "message": "Kayit basarili. Telefonunuza gelen kodu girin.",
    }


@router.post("/verify-otp")
def verify_otp(body: VerifyOTPRequest, db=Depends(get_db)):
    """Verify phone OTP."""
    phone = _normalize_phone(body.phone)
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT id, otp_code, otp_expires_at, otp_attempts, otp_locked_until FROM users WHERE phone = %s",
        (phone,),
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(400, "Kullanıcı bulunamadı")

    # Check lock
    if user["otp_locked_until"] and user["otp_locked_until"] > datetime.utcnow():
        remaining = (user["otp_locked_until"] - datetime.utcnow()).seconds // 60
        raise HTTPException(429, f"Çok fazla deneme. {remaining + 1} dakika sonra tekrar deneyin.")

    # Check expiry
    if not user["otp_expires_at"] or user["otp_expires_at"] < datetime.utcnow():
        raise HTTPException(400, "OTP süresi dolmuş. Tekrar gönder butonunu kullanın.")

    # Check code
    if _hash_otp(body.otp) != user["otp_code"]:
        attempts = (user["otp_attempts"] or 0) + 1
        if attempts >= 3:
            cur.execute(
                "UPDATE users SET otp_attempts = %s, otp_locked_until = %s WHERE id = %s",
                (attempts, datetime.utcnow() + timedelta(minutes=10), user["id"]),
            )
        else:
            cur.execute("UPDATE users SET otp_attempts = %s WHERE id = %s", (attempts, user["id"]))
        db.commit()
        remaining = 3 - attempts
        raise HTTPException(400, f"Yanlış kod. {remaining} hak kaldı." if remaining > 0 else "Çok fazla yanlış deneme. 10 dakika bekleyin.")

    # Success
    cur.execute(
        "UPDATE users SET phone_verified = TRUE, otp_code = NULL, otp_expires_at = NULL, otp_attempts = 0, otp_locked_until = NULL WHERE id = %s",
        (user["id"],),
    )
    db.commit()

    token = create_token(user["id"])
    return {"ok": True, "token": token, "message": "Telefon dogrulandi"}


@router.post("/resend-otp")
def resend_otp(body: VerifyOTPRequest, db=Depends(get_db)):
    """Resend OTP. Rate limited: max 5/hour."""
    phone = _normalize_phone(body.phone)
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT id, otp_locked_until FROM users WHERE phone = %s", (phone,))
    user = cur.fetchone()
    if not user:
        raise HTTPException(400, "Kullanıcı bulunamadı")

    if user["otp_locked_until"] and user["otp_locked_until"] > datetime.utcnow():
        raise HTTPException(429, "Çok fazla deneme. Lütfen bekleyin.")

    otp = _generate_otp()
    cur.execute(
        "UPDATE users SET otp_code = %s, otp_expires_at = %s, otp_attempts = 0 WHERE id = %s",
        (_hash_otp(otp), datetime.utcnow() + timedelta(minutes=5), user["id"]),
    )
    db.commit()

    _send_otp_sms(phone, otp)
    return {"ok": True, "message": "Yeni kod gonderildi"}


@router.post("/login")
def login(body: LoginRequest, db=Depends(get_db)):
    """Login with email or phone + password."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    # Flutter sends "email" field, web/admin may send "identifier"
    identifier = (body.identifier or body.email or "").strip()

    # Detect email vs phone
    if '@' in identifier:
        cur.execute("SELECT id, email, password_hash, full_name, role FROM users WHERE email = %s", (identifier.lower(),))
    else:
        phone = _normalize_phone(identifier)
        cur.execute("SELECT id, email, password_hash, full_name, role FROM users WHERE phone = %s", (phone,))

    user = cur.fetchone()
    if not user:
        raise HTTPException(401, "E-posta veya şifre hatalı")

    if not _check_password(body.password, user["password_hash"]):
        raise HTTPException(401, "E-posta veya şifre hatalı")

    # Generate token
    expiry_days = 30 if body.remember_me else 1
    token = create_token(user["id"], expiry_days=expiry_days)

    # Store remember token if requested
    if body.remember_me:
        remember = secrets.token_urlsafe(48)
        remember_hash = hashlib.sha256(remember.encode()).hexdigest()
        cur.execute(
            "UPDATE users SET remember_token = %s, remember_token_expires_at = %s WHERE id = %s",
            (remember_hash, datetime.utcnow() + timedelta(days=30), user["id"]),
        )
        db.commit()

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    }


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db=Depends(get_db)):
    """Step 1: Send reset via email or phone."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    if body.method == 'email':
        cur.execute("SELECT id, email FROM users WHERE email = %s", (body.identifier.lower().strip(),))
        user = cur.fetchone()
        if not user:
            return {"ok": True, "message": "E-postanizi kontrol edin"}  # Don't reveal if exists
        token = secrets.token_urlsafe(48)
        cur.execute(
            "UPDATE users SET email_verification_token = %s, email_verification_expires_at = %s WHERE id = %s",
            (token, datetime.utcnow() + timedelta(hours=1), user["id"]),
        )
        db.commit()
        _send_verification_email(user["email"], token)
        return {"ok": True, "message": "E-postanizi kontrol edin"}

    elif body.method == 'phone':
        phone = _normalize_phone(body.identifier)
        cur.execute("SELECT id FROM users WHERE phone = %s", (phone,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(400, "Kullanıcı bulunamadı")
        otp = _generate_otp()
        cur.execute(
            "UPDATE users SET otp_code = %s, otp_expires_at = %s, otp_attempts = 0 WHERE id = %s",
            (_hash_otp(otp), datetime.utcnow() + timedelta(minutes=5), user["id"]),
        )
        db.commit()
        _send_otp_sms(phone, otp)
        return {"ok": True, "masked_phone": _mask_phone(phone), "message": "Telefonunuza kod gonderildi"}

    raise HTTPException(400, "Geçersiz method")


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db=Depends(get_db)):
    """Set new password after OTP or email verification."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    if len(body.new_password) < 8:
        raise HTTPException(400, "Şifre en az 8 karakter olmalı")

    user = None

    # Via phone OTP
    if body.phone and body.otp:
        phone = _normalize_phone(body.phone)
        cur.execute("SELECT id, otp_code, otp_expires_at FROM users WHERE phone = %s", (phone,))
        user = cur.fetchone()
        if not user or not user["otp_code"] or _hash_otp(body.otp) != user["otp_code"]:
            raise HTTPException(400, "Geçersiz kod")
        if user["otp_expires_at"] and user["otp_expires_at"] < datetime.utcnow():
            raise HTTPException(400, "Kod süresi dolmuş")

    # Via email token
    elif body.token:
        cur.execute("SELECT id FROM users WHERE email_verification_token = %s AND email_verification_expires_at > NOW()", (body.token,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(400, "Geçersiz veya süresi dolmuş link")

    if not user:
        raise HTTPException(400, "Dogrulama bilgisi gerekli")

    password_hash = _hash_password(body.new_password)
    cur.execute(
        "UPDATE users SET password_hash = %s, otp_code = NULL, email_verification_token = NULL WHERE id = %s",
        (password_hash, user["id"]),
    )
    db.commit()

    return {"ok": True, "message": "Sifre basariyla guncellendi"}


@router.get("/verify-email/{token}")
def verify_email(token: str, db=Depends(get_db)):
    """Email verification via magic link."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id FROM users WHERE email_verification_token = %s AND email_verification_expires_at > NOW()",
        (token,),
    )
    user = cur.fetchone()
    if not user:
        return {"ok": False, "message": "Geçersiz veya süresi dolmuş link"}

    cur.execute(
        "UPDATE users SET email_verified = TRUE, email_verification_token = NULL WHERE id = %s",
        (user["id"],),
    )
    db.commit()
    return {"ok": True, "message": "E-posta dogrulandi!"}
