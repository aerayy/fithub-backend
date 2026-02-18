"""
WebSocket endpoint for real-time messaging.
Connect: ws(s)://<host>/ws?token=<jwt>

Message types (client → server):
  {"type": "message", "conversation_id": 1, "body": "hi", "message_type": "text"}
  {"type": "message", "conversation_id": 1, "message_type": "image", "media_url": "...", "media_metadata": {...}}
  {"type": "typing", "conversation_id": 1}
  {"type": "read", "conversation_id": 1, "message_id": 42}
  {"type": "ping"}

Message types (server → client):
  {"type": "connected", "user_id": 5, "conversation_ids": [1,2]}
  {"type": "new_message", "conversation_id": 1, "message": {...}}
  {"type": "typing", "conversation_id": 1, "user_id": 3}
  {"type": "message_read", "conversation_id": 1, "message_id": 42}
  {"type": "pong"}
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
from psycopg2.extras import RealDictCursor, Json
import psycopg2

from app.core.config import JWT_SECRET, JWT_ALGORITHM, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from app.core.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_db():
    """Direct DB connection for WebSocket context (no FastAPI Depends)."""
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        host=DB_HOST, port=int(DB_PORT),
        cursor_factory=RealDictCursor,
    )


def _authenticate_token(token: str):
    """Decode JWT and return user dict or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        conn = _get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, email, role FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        conn.close()
        return dict(user) if user else None
    except Exception as e:
        logger.warning(f"WS auth failed: {e}")
        return None


def _ts(val):
    """Convert timestamp to ISO string."""
    if val and hasattr(val, "isoformat"):
        return val.isoformat()
    return val


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # Authenticate
    user = _authenticate_token(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    user_id = user["id"]

    await manager.connect(websocket, user_id)

    # Send connection confirmation with conversation IDs
    try:
        conn = _get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM conversations WHERE client_user_id = %s OR coach_user_id = %s",
            (user_id, user_id),
        )
        conv_ids = [r["id"] for r in (cur.fetchall() or [])]
        conn.close()

        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "conversation_ids": conv_ids,
        })
    except Exception as e:
        logger.error(f"WS init error: {e}")

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "message":
                await _handle_send_message(user_id, user["role"], data)
            elif msg_type == "typing":
                await _handle_typing(user_id, data)
            elif msg_type == "read":
                await _handle_read(user_id, user["role"], data)
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WS error user_id={user_id}: {e}")
        manager.disconnect(websocket, user_id)


async def _handle_send_message(sender_id: int, sender_role: str, data: dict):
    """Save message to DB and broadcast to both participants."""
    conversation_id = data.get("conversation_id")
    body = data.get("body")
    message_type = data.get("message_type", "text")
    media_url = data.get("media_url")
    media_metadata = data.get("media_metadata")

    if not conversation_id:
        return
    if message_type == "text" and (not body or not str(body).strip()):
        return
    if message_type == "image" and not media_url:
        return

    body = str(body).strip() if body else None

    conn = _get_db()
    cur = conn.cursor()

    try:
        # Verify sender belongs to conversation
        cur.execute(
            "SELECT client_user_id, coach_user_id FROM conversations WHERE id = %s",
            (conversation_id,),
        )
        conv = cur.fetchone()
        if not conv or sender_id not in (conv["client_user_id"], conv["coach_user_id"]):
            return

        sender_type = "coach" if sender_id == conv["coach_user_id"] else "client"
        recipient_id = conv["client_user_id"] if sender_type == "coach" else conv["coach_user_id"]

        cur.execute(
            """
            INSERT INTO messages
                (conversation_id, sender_type, sender_user_id, body, message_type, media_url, media_metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id, sender_type, sender_user_id, body, message_type, media_url, media_metadata, created_at, read_at
            """,
            (
                conversation_id, sender_type, sender_id, body,
                message_type, media_url,
                Json(media_metadata) if media_metadata else None,
            ),
        )
        row = cur.fetchone()
        conn.commit()

        msg_payload = {
            "type": "new_message",
            "conversation_id": conversation_id,
            "message": {
                "id": row["id"],
                "sender_type": row["sender_type"],
                "sender_user_id": row["sender_user_id"],
                "body": row["body"],
                "message_type": row["message_type"],
                "media_url": row["media_url"],
                "media_metadata": row["media_metadata"],
                "created_at": _ts(row["created_at"]),
                "read_at": None,
            },
        }

        await manager.send_to_user(sender_id, msg_payload)
        await manager.send_to_user(recipient_id, msg_payload)

    except Exception as e:
        logger.error(f"WS _handle_send_message error: {e}")
        conn.rollback()
    finally:
        conn.close()


async def _handle_typing(sender_id: int, data: dict):
    """Broadcast typing indicator to the other participant."""
    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return

    conn = _get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT client_user_id, coach_user_id FROM conversations WHERE id = %s",
            (conversation_id,),
        )
        conv = cur.fetchone()
        if not conv or sender_id not in (conv["client_user_id"], conv["coach_user_id"]):
            return

        recipient_id = (
            conv["client_user_id"]
            if sender_id == conv["coach_user_id"]
            else conv["coach_user_id"]
        )

        await manager.send_to_user(recipient_id, {
            "type": "typing",
            "conversation_id": conversation_id,
            "user_id": sender_id,
        })
    finally:
        conn.close()


async def _handle_read(user_id: int, user_role: str, data: dict):
    """Mark a message as read and notify the sender."""
    conversation_id = data.get("conversation_id")
    message_id = data.get("message_id")
    if not conversation_id or not message_id:
        return

    other_type = "client" if user_role == "coach" else "coach"

    conn = _get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE messages SET read_at = NOW()
            WHERE id = %s AND conversation_id = %s AND sender_type = %s AND read_at IS NULL
            RETURNING sender_user_id
            """,
            (message_id, conversation_id, other_type),
        )
        row = cur.fetchone()
        conn.commit()

        if row:
            await manager.send_to_user(row["sender_user_id"], {
                "type": "message_read",
                "conversation_id": conversation_id,
                "message_id": message_id,
            })
    except Exception as e:
        logger.error(f"WS _handle_read error: {e}")
        conn.rollback()
    finally:
        conn.close()
