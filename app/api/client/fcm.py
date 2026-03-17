"""FCM token registration endpoints for push notifications."""
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


class FcmTokenRequest(BaseModel):
    fcm_token: str
    platform: str = "android"  # android, ios, web


@router.post("/fcm-token")
def register_fcm_token(
    body: FcmTokenRequest,
    db=Depends(get_db),
    current_user=Depends(require_role("client", "coach")),
):
    """Register FCM token for push notifications."""
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO fcm_tokens (user_id, fcm_token, platform, updated_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (user_id, fcm_token) DO UPDATE SET
            platform = EXCLUDED.platform,
            updated_at = NOW()
        """,
        (current_user["id"], body.fcm_token, body.platform),
    )
    db.commit()
    return {"ok": True}


@router.delete("/fcm-token")
def unregister_fcm_token(
    fcm_token: str,
    db=Depends(get_db),
    current_user=Depends(require_role("client", "coach")),
):
    """Remove FCM token (on logout)."""
    cur = db.cursor()
    cur.execute(
        "DELETE FROM fcm_tokens WHERE user_id = %s AND fcm_token = %s",
        (current_user["id"], fcm_token),
    )
    db.commit()
    return {"ok": True}
