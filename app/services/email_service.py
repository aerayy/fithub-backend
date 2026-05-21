"""Resend email gönderme servisi.

Kullanım:
    from app.services.email_service import send_email
    await send_email(
        to="user@example.com",
        subject="Hoş geldin",
        html="<h1>Merhaba</h1>",
    )

Configuration:
    RESEND_API_KEY env var olmadan init atlanır, send_email no-op olur.
    EMAIL_FROM env var ile sender override edilebilir.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
_FROM_EMAIL = os.getenv("EMAIL_FROM", "FitHub <noreply@fithubpoint.com>")
_DEFAULT_REPLY_TO = os.getenv("EMAIL_REPLY_TO", "support@fithubpoint.com")

_resend_client = None
if _API_KEY:
    try:
        import resend as _resend
        _resend.api_key = _API_KEY
        _resend_client = _resend
        logger.info("Resend initialized with sender=%s", _FROM_EMAIL)
    except Exception as e:
        logger.error("Resend init failed: %s", e)
else:
    logger.warning("RESEND_API_KEY not set — email_service will no-op")


def send_email(
    to: str,
    subject: str,
    html: str,
    *,
    from_addr: Optional[str] = None,
    reply_to: Optional[str] = None,
    text: Optional[str] = None,
) -> dict:
    """Senkron Resend send. Resend SDK kendisi async desteklemiyor, sync OK.

    Args:
        to: Alıcı email adresi (tek alıcı)
        subject: Konu
        html: HTML gövde
        from_addr: Override sender (default: EMAIL_FROM env)
        reply_to: Reply-To adresi (kullanıcının cevap atmasını istiyorsan)
        text: Plain text fallback (HTML render edemeyen client'lar için)

    Returns:
        dict — Resend response veya {"skipped": True, "reason": ...}
    """
    if not _resend_client:
        logger.warning("send_email skipped — Resend not initialized (to=%s)", to)
        return {"skipped": True, "reason": "resend_not_initialized"}

    if not to or "@" not in to:
        logger.error("send_email: invalid recipient %r", to)
        return {"skipped": True, "reason": "invalid_recipient"}

    params = {
        "from": from_addr or _FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
        "reply_to": reply_to or _DEFAULT_REPLY_TO,
    }
    if text:
        params["text"] = text

    try:
        response = _resend_client.Emails.send(params)
        email_id = response.get("id") if isinstance(response, dict) else None
        logger.info("Email sent to=%s subject=%r id=%s", to, subject[:60], email_id)
        return response
    except Exception as e:
        logger.exception("send_email failed to=%s: %s", to, e)
        return {"error": str(e)[:200], "skipped": False}


# Convenience templates — stubs for future use
def render_welcome_email(user_name: str) -> str:
    """Basit hoş geldin email HTML'i."""
    safe_name = (user_name or "FitHub'lı").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>FitHub'a Hoş Geldin</title></head>
<body style="font-family: -apple-system, sans-serif; background: #0C0C0E; color: #ECECEC; padding: 32px;">
  <div style="max-width: 480px; margin: 0 auto; background: #16161A; border-radius: 16px; padding: 32px;">
    <h1 style="color: #3E9E8E; margin-top: 0;">Merhaba {safe_name},</h1>
    <p>FitHub'a hoş geldin! Senin için kişiselleştirilmiş antrenman ve beslenme programları hazırlıyoruz.</p>
    <p style="color: #888; font-size: 13px; margin-top: 32px;">— FitHub Ekibi</p>
  </div>
</body>
</html>"""


def render_password_reset_email(reset_url: str) -> str:
    """Şifre sıfırlama email HTML'i."""
    return f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Şifre Sıfırlama</title></head>
<body style="font-family: -apple-system, sans-serif; background: #0C0C0E; color: #ECECEC; padding: 32px;">
  <div style="max-width: 480px; margin: 0 auto; background: #16161A; border-radius: 16px; padding: 32px;">
    <h1 style="color: #3E9E8E; margin-top: 0;">Şifre Sıfırlama</h1>
    <p>Şifre sıfırlama talebinde bulundun. Devam etmek için aşağıdaki butona tıkla:</p>
    <p style="text-align: center; margin: 32px 0;">
      <a href="{reset_url}" style="background: #3E9E8E; color: #0C0C0E; padding: 14px 28px; border-radius: 10px; text-decoration: none; font-weight: bold;">Şifremi Sıfırla</a>
    </p>
    <p style="color: #888; font-size: 12px;">Bu talebi sen yapmadıysan bu e-postayı görmezden gelebilirsin.</p>
    <p style="color: #888; font-size: 13px; margin-top: 32px;">— FitHub Ekibi</p>
  </div>
</body>
</html>"""


def render_email_verification(verification_url: str) -> str:
    """Email doğrulama email HTML'i."""
    return f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>E-posta Doğrulama</title></head>
<body style="font-family: -apple-system, sans-serif; background: #0C0C0E; color: #ECECEC; padding: 32px;">
  <div style="max-width: 480px; margin: 0 auto; background: #16161A; border-radius: 16px; padding: 32px;">
    <h1 style="color: #3E9E8E; margin-top: 0;">E-posta Doğrulama</h1>
    <p>FitHub hesabını doğrulamak için aşağıdaki butona tıkla:</p>
    <p style="text-align: center; margin: 32px 0;">
      <a href="{verification_url}" style="background: #3E9E8E; color: #0C0C0E; padding: 14px 28px; border-radius: 10px; text-decoration: none; font-weight: bold;">E-postamı Doğrula</a>
    </p>
    <p style="color: #888; font-size: 12px;">Bu hesabı sen oluşturmadıysan bu e-postayı görmezden gelebilirsin.</p>
    <p style="color: #888; font-size: 13px; margin-top: 32px;">— FitHub Ekibi</p>
  </div>
</body>
</html>"""
