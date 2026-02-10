"""
Coach-side messaging: list conversations, get messages, send messages, mark read.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional, List

from app.core.database import get_db
from app.core.security import require_role

logger = logging.getLogger(__name__)
router = APIRouter()


class SendMessageBody(BaseModel):
    body: str  # validated non-empty (see validator)

    @field_validator("body", mode="before")
    @classmethod
    def body_non_empty(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("body must be a string")
        s = v.strip()
        if not s:
            raise ValueError("body cannot be empty")
        return s


def _ensure_coach_conversation(cur, conversation_id: int, coach_user_id: int) -> dict:
    cur.execute(
        "SELECT id, client_user_id, coach_user_id FROM conversations WHERE id = %s",
        (conversation_id,),
    )
    row = cur.fetchone()
    if not row or row["coach_user_id"] != coach_user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return dict(row)


@router.get("/conversations")
def list_coach_conversations(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """List conversations for the current coach."""
    coach_user_id = current_user["id"]
    cur = db.cursor()

    cur.execute(
        """
        SELECT
            c.id,
            c.client_user_id,
            COALESCE(u.full_name, u.email) AS client_name,
            (SELECT body FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) AS last_message_preview,
            (SELECT created_at FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) AS last_message_at,
            (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id AND m.sender_type = 'client' AND m.read_at IS NULL) AS unread_count
        FROM conversations c
        JOIN users u ON u.id = c.client_user_id
        WHERE c.coach_user_id = %s
        ORDER BY last_message_at DESC NULLS LAST
        """,
        (coach_user_id,),
    )
    rows = cur.fetchall() or []

    conversations = []
    for r in rows:
        conversations.append({
            "id": r["id"],
            "client_user_id": r["client_user_id"],
            "client_name": r["client_name"],
            "last_message_preview": (r["last_message_preview"] or "")[:100] if r.get("last_message_preview") else None,
            "last_message_at": r["last_message_at"].isoformat() if r.get("last_message_at") and hasattr(r["last_message_at"], "isoformat") else r.get("last_message_at"),
            "unread_count": r.get("unread_count") or 0,
        })
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}/messages")
def list_coach_messages(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[int] = Query(None, description="message_id for pagination"),
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Get messages for a conversation. Newest first."""
    coach_user_id = current_user["id"]
    cur = db.cursor()
    _ensure_coach_conversation(cur, conversation_id, coach_user_id)

    if before:
        cur.execute(
            """
            SELECT id, sender_type, body, created_at, read_at
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
            SELECT id, sender_type, body, created_at, read_at
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
            "created_at": r["created_at"].isoformat() if r.get("created_at") and hasattr(r["created_at"], "isoformat") else r.get("created_at"),
            "read_at": r["read_at"].isoformat() if r.get("read_at") and hasattr(r["read_at"], "isoformat") else r.get("read_at"),
        })
    return {"messages": messages, "has_more": has_more}


@router.post("/conversations/{conversation_id}/messages")
def send_coach_message(
    conversation_id: int,
    body: SendMessageBody,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Send a message as coach."""
    coach_user_id = current_user["id"]
    cur = db.cursor()
    _ensure_coach_conversation(cur, conversation_id, coach_user_id)

    cur.execute(
        """
        INSERT INTO messages (conversation_id, sender_type, sender_user_id, body, created_at)
        VALUES (%s, 'coach', %s, %s, NOW())
        RETURNING id, sender_type, body, created_at, read_at
        """,
        (conversation_id, coach_user_id, body.body.strip()),
    )
    row = cur.fetchone()
    db.commit()
    return {
        "id": row["id"],
        "sender_type": row["sender_type"],
        "body": row["body"],
        "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else row["created_at"],
        "read_at": row["read_at"].isoformat() if row.get("read_at") and hasattr(row["read_at"], "isoformat") else row.get("read_at"),
    }


@router.patch("/conversations/{conversation_id}/messages/{message_id}/read")
def mark_coach_message_read(
    conversation_id: int,
    message_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Mark a message as read. Only for messages sent by client."""
    coach_user_id = current_user["id"]
    cur = db.cursor()
    _ensure_coach_conversation(cur, conversation_id, coach_user_id)

    cur.execute(
        """
        UPDATE messages
        SET read_at = NOW()
        WHERE id = %s AND conversation_id = %s AND sender_type = 'client' AND read_at IS NULL
        RETURNING id
        """,
        (message_id, conversation_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Message not found or already read")
    db.commit()
    return {"ok": True}
