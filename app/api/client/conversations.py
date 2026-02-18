"""
Client-side messaging: list conversations, get/create conversation, send messages, mark read.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional, List
from psycopg2.extras import Json

from app.core.database import get_db
from app.core.security import require_role
from .routes import router

logger = logging.getLogger(__name__)


# ---- Schemas ----
class CreateConversationBody(BaseModel):
    coach_user_id: Optional[int] = None


class SendMessageBody(BaseModel):
    body: Optional[str] = None
    message_type: str = "text"
    media_url: Optional[str] = None
    media_metadata: Optional[dict] = None

    @field_validator("body", mode="before")
    @classmethod
    def body_non_empty(cls, v, info):
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("body must be a string")
        s = v.strip()
        return s if s else None

    @field_validator("message_type", mode="before")
    @classmethod
    def validate_message_type(cls, v):
        if v not in ("text", "image"):
            raise ValueError("message_type must be 'text' or 'image'")
        return v


def _ensure_client_conversation(cur, conversation_id: int, client_user_id: int) -> dict:
    cur.execute(
        "SELECT id, client_user_id, coach_user_id FROM conversations WHERE id = %s",
        (conversation_id,),
    )
    row = cur.fetchone()
    if not row or row["client_user_id"] != client_user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return dict(row)


def _get_client_active_coach(cur, client_user_id: int):
    """Return (coach_user_id, subscription_id) if client has active subscription with a coach."""
    cur.execute(
        """
        SELECT coach_user_id, id AS subscription_id
        FROM subscriptions
        WHERE client_user_id = %s
          AND status = 'active'
          AND (ends_at IS NULL OR ends_at > NOW())
        ORDER BY purchased_at DESC NULLS LAST, id DESC
        LIMIT 1
        """,
        (client_user_id,),
    )
    return cur.fetchone()


@router.get("/conversations")
def list_client_conversations(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """List conversations for the current client. Optionally auto-create one with their coach."""
    client_user_id = current_user["id"]
    cur = db.cursor()

    cur.execute(
        """
        SELECT
            c.id,
            c.coach_user_id,
            COALESCE(u.full_name, u.email) AS coach_name,
            (SELECT CASE WHEN message_type = 'image' THEN '[Foto]' ELSE body END FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) AS last_message_preview,
            (SELECT created_at FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) AS last_message_at,
            (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id AND m.sender_type = 'coach' AND m.read_at IS NULL) AS unread_count
        FROM conversations c
        JOIN users u ON u.id = c.coach_user_id
        WHERE c.client_user_id = %s
        ORDER BY last_message_at DESC NULLS LAST
        """,
        (client_user_id,),
    )
    rows = cur.fetchall() or []

    # Auto-create conversation with coach if none exists and client has active subscription
    if not rows:
        sub = _get_client_active_coach(cur, client_user_id)
        if sub:
            coach_user_id = sub["coach_user_id"]
            subscription_id = sub.get("subscription_id")
            cur.execute(
                """
                INSERT INTO conversations (client_user_id, coach_user_id, subscription_id, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (client_user_id, coach_user_id) DO UPDATE SET updated_at = NOW()
                RETURNING id, client_user_id, coach_user_id
                """,
                (client_user_id, coach_user_id, subscription_id),
            )
            new_row = cur.fetchone()
            if new_row:
                cur.execute(
                    """
                    SELECT
                        c.id,
                        c.coach_user_id,
                        COALESCE(u.full_name, u.email) AS coach_name,
                        NULL AS last_message_preview,
                        NULL AS last_message_at,
                        0 AS unread_count
                    FROM conversations c
                    JOIN users u ON u.id = c.coach_user_id
                    WHERE c.id = %s
                    """,
                    (new_row["id"],),
                )
                rows = cur.fetchall() or []
            db.commit()

    conversations = []
    for r in rows:
        conversations.append({
            "id": r["id"],
            "coach_user_id": r["coach_user_id"],
            "coach_name": r["coach_name"],
            "last_message_preview": (r["last_message_preview"] or "")[:100] if r.get("last_message_preview") else None,
            "last_message_at": r["last_message_at"].isoformat() if r.get("last_message_at") and hasattr(r["last_message_at"], "isoformat") else r.get("last_message_at"),
            "unread_count": r.get("unread_count") or 0,
        })
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}/messages")
def list_client_messages(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[int] = Query(None, description="message_id for pagination"),
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Get messages for a conversation. Newest first. before=<id> for older page."""
    client_user_id = current_user["id"]
    cur = db.cursor()
    _ensure_client_conversation(cur, conversation_id, client_user_id)

    if before:
        cur.execute(
            """
            SELECT id, sender_type, body, message_type, media_url, media_metadata, created_at, read_at
            FROM messages
            WHERE conversation_id = %s AND id < %s
            ORDER BY id DESC
            LIMIT %s
            """,
            (conversation_id, before, limit + 1),
        )
    else:
        cur.execute(
            """
            SELECT id, sender_type, body, message_type, media_url, media_metadata, created_at, read_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY id DESC
            LIMIT %s
            """,
            (conversation_id, limit + 1),
        )
    rows = cur.fetchall() or []
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]
    messages = []
    for r in rows:
        messages.append({
            "id": r["id"],
            "sender_type": r["sender_type"],
            "body": r["body"],
            "message_type": r.get("message_type", "text"),
            "media_url": r.get("media_url"),
            "media_metadata": r.get("media_metadata"),
            "created_at": r["created_at"].isoformat() if r.get("created_at") and hasattr(r["created_at"], "isoformat") else r.get("created_at"),
            "read_at": r["read_at"].isoformat() if r.get("read_at") and hasattr(r["read_at"], "isoformat") else r.get("read_at"),
        })
    return {"messages": messages, "has_more": has_more}


@router.post("/conversations")
def create_client_conversation(
    body: CreateConversationBody,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Find or create conversation with a coach. Client must have active subscription with that coach."""
    client_user_id = current_user["id"]
    coach_user_id = body.coach_user_id
    cur = db.cursor()

    if not coach_user_id:
        sub = _get_client_active_coach(cur, client_user_id)
        if not sub:
            raise HTTPException(status_code=400, detail="No active subscription with a coach")
        coach_user_id = sub["coach_user_id"]
        subscription_id = sub.get("subscription_id")
    else:
        cur.execute(
            """
            SELECT id FROM subscriptions
            WHERE client_user_id = %s AND coach_user_id = %s
              AND status = 'active' AND (ends_at IS NULL OR ends_at > NOW())
            LIMIT 1
            """,
            (client_user_id, coach_user_id),
        )
        sub = cur.fetchone()
        if not sub:
            raise HTTPException(status_code=403, detail="No active subscription with this coach")
        subscription_id = sub.get("id")

    cur.execute(
        """
        INSERT INTO conversations (client_user_id, coach_user_id, subscription_id, updated_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (client_user_id, coach_user_id) DO UPDATE SET updated_at = NOW()
        RETURNING id, client_user_id, coach_user_id
        """,
        (client_user_id, coach_user_id, subscription_id),
    )
    row = cur.fetchone()
    db.commit()
    cur.execute(
        "SELECT COALESCE(full_name, email) AS coach_name FROM users WHERE id = %s",
        (coach_user_id,),
    )
    name_row = cur.fetchone()
    return {
        "conversation": {
            "id": row["id"],
            "coach_user_id": row["coach_user_id"],
            "coach_name": name_row["coach_name"] if name_row else None,
        }
    }


@router.post("/conversations/{conversation_id}/messages")
def send_client_message(
    conversation_id: int,
    body: SendMessageBody,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Send a message as client. Sets read_at=now for the new message."""
    client_user_id = current_user["id"]
    cur = db.cursor()
    _ensure_client_conversation(cur, conversation_id, client_user_id)

    # Validate: text messages need body, image messages need media_url
    if body.message_type == "text" and not body.body:
        raise HTTPException(status_code=400, detail="body cannot be empty for text messages")
    if body.message_type == "image" and not body.media_url:
        raise HTTPException(status_code=400, detail="media_url required for image messages")

    cur.execute(
        """
        INSERT INTO messages (conversation_id, sender_type, sender_user_id, body, message_type, media_url, media_metadata, created_at, read_at)
        VALUES (%s, 'client', %s, %s, %s, %s, %s, NOW(), NOW())
        RETURNING id, sender_type, body, message_type, media_url, media_metadata, created_at, read_at
        """,
        (
            conversation_id, client_user_id, body.body,
            body.message_type, body.media_url,
            Json(body.media_metadata) if body.media_metadata else None,
        ),
    )
    row = cur.fetchone()
    db.commit()
    return {
        "id": row["id"],
        "sender_type": row["sender_type"],
        "body": row["body"],
        "message_type": row.get("message_type", "text"),
        "media_url": row.get("media_url"),
        "media_metadata": row.get("media_metadata"),
        "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else row["created_at"],
        "read_at": row["read_at"].isoformat() if row.get("read_at") and hasattr(row["read_at"], "isoformat") else row.get("read_at"),
    }


@router.patch("/conversations/{conversation_id}/messages/{message_id}/read")
def mark_client_message_read(
    conversation_id: int,
    message_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Mark a message as read. Only for messages sent by coach."""
    client_user_id = current_user["id"]
    cur = db.cursor()
    _ensure_client_conversation(cur, conversation_id, client_user_id)

    cur.execute(
        """
        UPDATE messages
        SET read_at = NOW()
        WHERE id = %s AND conversation_id = %s AND sender_type = 'coach' AND read_at IS NULL
        RETURNING id
        """,
        (message_id, conversation_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Message not found or already read")
    db.commit()
    return {"ok": True}
