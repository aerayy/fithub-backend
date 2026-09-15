"""Auth v2 — complete authentication flow with OTP, email verification, remember me."""
import os
import hmac
import re
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import BackgroundTasks
from pydantic import BaseModel, field_validator
from typing import Optional
from psycopg2.extras import RealDictCursor
import bcrypt

from app.core.database import get_db
from app.core.security import create_token, decode_token, require_role
from app.core import rate_limit
from app.core.config import COACH_INVITE_CODE
from app.core.security import issue_refresh_token, refresh_token_hash, REFRESH_TOKEN_DAYS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth-v2"])


# ─── Models ───

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    password_confirm: str
    birthdate: str  # YYYY-MM-DD
    accepted_terms: bool = False  # KVKK + Kullanim Sartlari onayi (zorunlu)

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
        # +90 ulkekodu varsa cikar
        if cleaned.startswith('90') and len(cleaned) == 12:
            cleaned = cleaned[2:]
        # leading 0 varsa cikar (Flutter "05415418585" gonderiyor)
        if cleaned.startswith('0') and len(cleaned) == 11:
            cleaned = cleaned[1:]
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


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    new_password_confirm: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Şifre en az 8 karakter olmalı')
        if not re.search(r'[0-9]', v):
            raise ValueError('Şifre en az 1 rakam içermeli')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Şifre en az 1 harf içermeli')
        return v


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
    """Send OTP via SMS. NOT wired — SMS sağlayıcı entegrasyonu yok (Netgsm/Twilio).
    Signup'ta OTP adımı frontend'de bypass edildiğinden şu an bloklayıcı değil.
    Telefonla şifre sıfırlama SMS gerektirir; sağlayıcı gelince burası kablolanmalı."""
    if os.getenv("RENDER_SERVICE_NAME"):
        logger.warning("SMS OTP requested but no SMS provider configured (phone=%s)", _mask_phone(phone))
    else:
        print(f'[SMS] OTP {otp} sent to {phone}')


def _send_verification_email(email: str, token: str):
    """E-posta doğrulama magic-link'i (GET /auth/verify-email/{token}) gönder.
    Resend üzerinden (email_service). RESEND_API_KEY yoksa email_service no-op döner."""
    link = f'https://fithub-backend-jd40.onrender.com/auth/verify-email/{token}'
    try:
        from app.services.email_service import send_email, render_email_verification
        send_email(
            to=email,
            subject="Fithub Point — E-posta adresini doğrula",
            html=render_email_verification(link),
        )
    except Exception:
        logger.exception("verification email send failed to=%s", email)


def _send_password_reset_email(email: str, token: str):
    """Şifre sıfırlama e-postası — landing'deki sıfırlama sayfasına yönlendirir
    (kullanıcı yeni şifre girer, sayfa POST /auth/reset-password çağırır)."""
    reset_url = f'https://fithubpoint.com/sifre-sifirla.html?token={token}'
    try:
        from app.services.email_service import send_email, render_password_reset_email
        send_email(
            to=email,
            subject="Fithub Point — Şifre sıfırlama",
            html=render_password_reset_email(reset_url),
        )
    except Exception:
        logger.exception("password reset email send failed to=%s", email)


# ─── Endpoints ───

@router.post("/register", dependencies=[rate_limit.rate_limited("register", 10, 3600)])
def register(body: RegisterRequest, db=Depends(get_db)):
    """Register new user with OTP + email verification."""
    cur = db.cursor(cursor_factory=RealDictCursor)

    # KVKK + Kullanim Sartlari onayi zorunlu
    if not body.accepted_terms:
        raise HTTPException(400, "Devam etmek için kullanım şartlarını ve KVKK aydınlatma metnini kabul etmelisiniz.")

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
           accepted_terms_at, created_at)
           VALUES (%s, %s, %s, %s, 'client', %s,
           FALSE, FALSE,
           %s, %s, 0,
           %s, %s,
           NOW(), NOW())
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
    try:
        refresh = issue_refresh_token(cur, user_id)
        db.commit()
    except Exception:
        refresh = None

    return {
        "ok": True,
        "user_id": user_id,
        "token": token,
        "refresh_token": refresh,
        "masked_phone": _mask_phone(body.phone),
        "message": "Kayit basarili. Telefonunuza gelen kodu girin.",
    }


@router.post("/verify-otp", dependencies=[rate_limit.rate_limited("verify_otp", 20, 600)])
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


@router.post("/resend-otp", dependencies=[rate_limit.rate_limited("resend_otp", 5, 600)])
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


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", dependencies=[rate_limit.rate_limited("refresh", 60, 600)])
def refresh_access_token(body: RefreshRequest, db=Depends(get_db)):
    """Refresh token ile yeni access token. 30 gün kayan pencere (süre uzatılır,
    token döndürülmez). Geçersiz/süresi dolmuş → 401 → istemci Login'e döner."""
    raw = (body.refresh_token or "").strip()
    if not raw or len(raw) > 512:
        raise HTTPException(401, "Geçersiz oturum, lütfen tekrar giriş yap.")
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id, remember_token_expires_at FROM users WHERE remember_token = %s",
        (refresh_token_hash(raw),),
    )
    user = cur.fetchone()
    exp = user["remember_token_expires_at"] if user else None
    # Kolon TIMESTAMP veya TIMESTAMPTZ olabilir (prod'da elle eklendi) — ikisini de karşılaştır
    now = datetime.now(exp.tzinfo) if (exp is not None and exp.tzinfo is not None) else datetime.utcnow()
    if not user or not exp or exp < now:
        raise HTTPException(401, "Oturum süresi doldu, lütfen tekrar giriş yap.")
    cur.execute(
        "UPDATE users SET remember_token_expires_at = %s WHERE id = %s",
        (datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS), user["id"]),
    )
    db.commit()
    return {"token": create_token(user["id"], expiry_days=REFRESH_TOKEN_DAYS), "refresh_token": raw}


@router.post("/login", dependencies=[rate_limit.rate_limited("login_ip", 30, 600)])
def login(body: LoginRequest, db=Depends(get_db)):
    """Login with email or phone + password."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    # Flutter sends "email" field, web/admin may send "identifier"
    identifier = (body.identifier or body.email or "").strip()
    # Hesap hedefli şifre denemesi: aynı kimlik için 10 dk'da en fazla 8 deneme
    if identifier:
        rate_limit.check("login_id", identifier.lower(), 8, 600, db=db)

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

    # Kalıcı oturum: remember_me ise refresh token ver (istemci güvenli
    # depoda saklar, JWT bitince /auth/refresh ile sessizce yeniler)
    refresh = None
    if body.remember_me:
        refresh = issue_refresh_token(cur, user["id"])
        db.commit()

    return {
        "token": token,
        "refresh_token": refresh,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    }


@router.post("/forgot-password", dependencies=[rate_limit.rate_limited("forgot_pw", 5, 900)])
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
        _send_password_reset_email(user["email"], token)
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


@router.post("/reset-password", dependencies=[rate_limit.rate_limited("reset_pw", 10, 900)])
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


# ─── Change Password (logged-in user) ───

@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    current_user=Depends(require_role("client")),
    db=Depends(get_db),
):
    """Giriş yapmış kullanıcı için şifre değiştirme.
    Eski şifre doğrulanır, yeni şifre validate edilir, hash güncellenir."""
    if body.new_password != body.new_password_confirm:
        raise HTTPException(400, "Yeni şifreler eşleşmiyor")

    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT password_hash, auth_provider FROM users WHERE id = %s",
        (current_user["id"],),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Kullanıcı bulunamadı")

    if not row.get("password_hash"):
        # OAuth (Google/Apple) ile kayıt olan kullanıcının şifresi yok
        provider = row.get("auth_provider") or "OAuth"
        raise HTTPException(
            400,
            f"{provider.capitalize()} ile giriş yaptığınız için şifre değiştiremezsiniz.",
        )

    if not _check_password(body.old_password, row["password_hash"]):
        raise HTTPException(401, "Mevcut şifreniz hatalı")

    if body.old_password == body.new_password:
        raise HTTPException(400, "Yeni şifre eskisiyle aynı olamaz")

    new_hash = _hash_password(body.new_password)
    cur.execute(
        "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
        (new_hash, current_user["id"]),
    )
    db.commit()
    return {"ok": True, "message": "Şifreniz başarıyla değiştirildi"}


# ─── Health Disclaimer Acceptance (Apple Guideline 1.4.1) ───

@router.post("/accept-health-disclaimer")
def accept_health_disclaimer(
    current_user=Depends(require_role("client")),
    db=Depends(get_db),
):
    """Kullanıcı in-app sağlık uyarısı modal'ında "Kabul Et" tıklayınca çağrılır.
    accepted_health_disclaimer_at timestamp'i set edilir (idempotent — zaten
    set ise update edilmez)."""
    cur = db.cursor()
    cur.execute(
        """UPDATE users SET accepted_health_disclaimer_at = NOW()
           WHERE id = %s AND accepted_health_disclaimer_at IS NULL""",
        (current_user["id"],),
    )
    db.commit()
    return {"ok": True}


# ─── Account Deletion (Apple Guideline 5.1.1(v) + KVKK) ───

def _try_exec(cur, sql: str, params: tuple) -> bool:
    """Toleranslı DELETE: tablo/kolon yoksa SAVEPOINT'e dönüp devam eder.

    Neden: 'except Exception: pass' transaction'ı aborted bırakıyordu; sonraki
    tüm ifadeler InFailedSqlTransaction ile düşüyor, hesap silme 500 veriyordu
    (temiz kurulumda coach_reviews yokken smoke test yakaladı).
    """
    cur.execute("SAVEPOINT del_sp")
    try:
        cur.execute(sql, params)
        cur.execute("RELEASE SAVEPOINT del_sp")
        return True
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT del_sp")
        return False


@router.delete("/me")
def delete_my_account(
    background_tasks: BackgroundTasks,
    current_user=Depends(require_role("client")),
    db=Depends(get_db),
):
    """KVKK uyumlu hesap silme. Tüm kişisel veriler hard-delete edilir,
    yasal saklama yükümlülüğü olan ilişkiler (subscriptions, mesajlar)
    de silinir — kayıt için Apple/Google/iyzico tarafında zaten kopya var.

    Users tablosundaki satır anonymize edilir (email placeholder ile değiştirilir,
    foreign key referansları kırılmamak için satır silinmez, deleted_at=NOW).
    """
    user_id = current_user["id"]
    cur = db.cursor()

    # 0. Cloudinary'deki görselleri silmek için URL'leri ÖNCE topla (satırlar
    #    silinince URL'ler kaybolur). Silme işlemi commit sonrası arka planda.
    media_urls = []
    for _sql in (
        "SELECT profile_photo_url AS u FROM users WHERE id = %s",
        "SELECT photo_url AS u FROM body_form_photos WHERE client_user_id = %s",
        "SELECT photo_url AS u FROM meal_photos WHERE client_user_id = %s",
        "SELECT photo_url AS u FROM activity_log WHERE client_user_id = %s",
        "SELECT media_url AS u FROM messages WHERE sender_user_id = %s",
    ):
        try:
            cur.execute(_sql, (user_id,))
            media_urls.extend(r["u"] for r in (cur.fetchall() or []) if r.get("u"))
        except Exception:
            db.rollback()

    try:
        # 1. Kişisel veri tabloları — hard delete
        personal_data_deletes = [
            "DELETE FROM activity_log WHERE client_user_id = %s",
            "DELETE FROM body_form_photos WHERE client_user_id = %s",
            "DELETE FROM body_measurements WHERE user_id = %s",
            "DELETE FROM client_challenge_cache WHERE user_id = %s",
            "DELETE FROM client_motivation_cache WHERE user_id = %s",
            "DELETE FROM client_recovery_cache WHERE user_id = %s",
            "DELETE FROM client_onboarding WHERE user_id = %s",
            "DELETE FROM daily_water_log WHERE user_id = %s",
            "DELETE FROM fcm_tokens WHERE user_id = %s",
            "DELETE FROM form_analysis_settings WHERE client_user_id = %s",
            "DELETE FROM meal_photos WHERE client_user_id = %s",
            "DELETE FROM user_badges WHERE user_id = %s",
            "DELETE FROM nutrition_program_drafts WHERE client_user_id = %s",
            "DELETE FROM workout_program_drafts WHERE client_user_id = %s",
        ]
        # workout_sessions (varsa)
        _try_exec(cur, "DELETE FROM workout_sessions WHERE user_id = %s", (user_id,))

        for sql in personal_data_deletes:
            _try_exec(cur, sql, (user_id,))  # tablo/kolon yoksa atla, transaction bozulmaz

        # 2. Cascade: nutrition + workout + cardio programlar (alt tablolarla)
        _try_exec(cur,
            "DELETE FROM nutrition_meals WHERE nutrition_program_id IN "
            "(SELECT id FROM nutrition_programs WHERE client_user_id = %s)",
            (user_id,),
        )
        _try_exec(cur, "DELETE FROM nutrition_programs WHERE client_user_id = %s", (user_id,))

        # workout_programs varsa
        _try_exec(cur,
            "DELETE FROM workout_exercises WHERE workout_day_id IN "
            "(SELECT id FROM workout_days WHERE workout_program_id IN "
            "(SELECT id FROM workout_programs WHERE client_user_id = %s))",
            (user_id,),
        )
        _try_exec(cur,
            "DELETE FROM workout_days WHERE workout_program_id IN "
            "(SELECT id FROM workout_programs WHERE client_user_id = %s)",
            (user_id,),
        )
        _try_exec(cur, "DELETE FROM workout_programs WHERE client_user_id = %s", (user_id,))

        # cardio
        _try_exec(cur,
            "DELETE FROM cardio_sessions WHERE cardio_program_id IN "
            "(SELECT id FROM cardio_programs WHERE client_user_id = %s)",
            (user_id,),
        )
        _try_exec(cur, "DELETE FROM cardio_programs WHERE client_user_id = %s", (user_id,))

        # 3. Mesajlaşma + abonelik + değerlendirme — hard delete (NOT NULL FK'ler için)
        _try_exec(cur,
            "DELETE FROM messages WHERE conversation_id IN "
            "(SELECT id FROM conversations WHERE client_user_id = %s OR coach_user_id = %s)",
            (user_id, user_id),
        )
        _try_exec(cur, "DELETE FROM messages WHERE sender_user_id = %s", (user_id,))
        _try_exec(cur, "DELETE FROM conversations WHERE client_user_id = %s", (user_id,))
        _try_exec(cur, "DELETE FROM subscriptions WHERE client_user_id = %s", (user_id,))
        _try_exec(cur, "DELETE FROM coach_reviews WHERE client_user_id = %s", (user_id,))

        # 4. clients tablosundaki satır (assigned_coach_id ile koça referans)
        cur.execute("DELETE FROM clients WHERE user_id = %s", (user_id,))

        # 5. Users satırı — anonymize (FK referansları kırılmasın)
        #    email NOT NULL → unique placeholder ile değiştir, böylece bu kullanıcı
        #    bir daha login olamaz; aynı gerçek email ile yeni hesap açılabilir.
        placeholder_email = f"deleted-{user_id}-{int(datetime.utcnow().timestamp())}@deleted.local"
        cur.execute(
            """UPDATE users SET
                 email = %s,
                 password_hash = NULL,
                 full_name = NULL,
                 phone = NULL,
                 phone_number = NULL,
                 profile_photo_url = NULL,
                 email_verification_token = NULL,
                 otp_code = NULL,
                 otp_expires_at = NULL,
                 remember_token = NULL,
                 remember_token_expires_at = NULL,
                 auth_provider = NULL,
                 provider_user_id = NULL,
                 birthdate = NULL,
                 deleted_at = NOW()
               WHERE id = %s""",
            (placeholder_email, user_id),
        )

        db.commit()
        if media_urls:
            from app.services.media_cleanup import delete_cloudinary_assets
            background_tasks.add_task(delete_cloudinary_assets, media_urls)
        return {"ok": True, "message": "Hesabınız ve tüm verileriniz silindi."}
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger(__name__).exception("delete_my_account failed user_id=%s", user_id)
        raise HTTPException(status_code=500, detail="Hesap silinemedi. Lütfen tekrar deneyin.")


# ─── KVKK: veri taşınabilirliği (kendi verini indir) ───

@router.get("/me/export", dependencies=[rate_limit.rate_limited("export", 3, 3600)])
def export_my_data(
    current_user=Depends(require_role("client")),
    db=Depends(get_db),
):
    """Kullanıcının kendi verisini JSON olarak döndürür (KVKK m.11 erişim hakkı)."""
    from fastapi.encoders import jsonable_encoder
    from fastapi.responses import JSONResponse
    from app.services.data_export import build_export

    data = build_export(db, current_user["id"])
    return JSONResponse(
        content=jsonable_encoder(data),
        headers={"Content-Disposition": 'attachment; filename="fithub-verilerim.json"'},
    )


# ─── Koç self-signup (admin paneli /signup) ───
# Neden: panel, POST /admin/coaches'i tarayıcıya gömülü superadmin anahtarıyla
# çağırıyordu → anahtar herkese açıktı. Bu uç anahtar istemez; rate limit +
# (varsa) COACH_INVITE_CODE ile korunur, self-rating/is_active alanlarını kabul etmez.

class CoachSignupRequest(BaseModel):
    full_name: str
    email: str
    password: str
    invite_code: Optional[str] = None

    @field_validator('email')
    @classmethod
    def _v_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v or ""):
            raise ValueError('Geçersiz e-posta formatı')
        return v.lower().strip()

    @field_validator('password')
    @classmethod
    def _v_password(cls, v):
        if len(v or "") < 8:
            raise ValueError('Şifre en az 8 karakter olmalı')
        return v

    @field_validator('full_name')
    @classmethod
    def _v_name(cls, v):
        v = (v or "").strip()
        if len(v) < 2:
            raise ValueError('İsim en az 2 karakter olmalı')
        return v[:120]


@router.post("/coach-signup", dependencies=[rate_limit.rate_limited("coach_signup", 5, 3600)])
def coach_signup(body: CoachSignupRequest, db=Depends(get_db)):
    from app.api.admin import CreateCoachRequest, _create_coach_account
    from app.core.security import create_token

    if COACH_INVITE_CODE:
        if not body.invite_code or not hmac.compare_digest(body.invite_code.strip(), COACH_INVITE_CODE):
            raise HTTPException(status_code=403, detail="Davet kodu geçersiz.")

    try:
        req = CreateCoachRequest(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            bio="",
            instagram="",
            photo_url="",
            price_per_month=0,
            rating=0,
            rating_count=0,
            specialties=[],
            is_active=True,
        )
    except Exception:
        # CreateCoachRequest EmailStr kullanır (rezerve alan adlarını reddeder)
        raise HTTPException(status_code=422, detail="Geçersiz e-posta adresi.")
    created = _create_coach_account(req, db)
    user_id = created["user_id"]
    return {
        "token": create_token(user_id, expiry_days=7),
        "user_id": user_id,
        "user_email": body.email,
        "role": "coach",
    }
