"""
Push notification service using Firebase Cloud Messaging.
Sends notifications to client devices when:
- Workout program assigned/updated
- Nutrition program assigned/updated
- Coach sends a message
"""
import os
import json

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    _firebase_available = True
except ImportError:
    _firebase_available = False

# Initialize Firebase Admin SDK
_firebase_initialized = False

def _init_firebase():
    global _firebase_initialized
    if _firebase_initialized or not _firebase_available:
        return

    # Try service account file first, then env var
    sa_path = os.path.join(os.path.dirname(__file__), '../../firebase-service-account.json')
    sa_env = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')

    try:
        if os.path.exists(sa_path):
            cred = credentials.Certificate(sa_path)
        elif sa_env:
            sa_dict = json.loads(sa_env)
            cred = credentials.Certificate(sa_dict)
        else:
            print('[FCM] No Firebase credentials found, push notifications disabled')
            return

        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        print('[FCM] Firebase Admin SDK initialized')
    except Exception as e:
        print(f'[FCM] Firebase init error: {e}')


def _get_user_tokens(user_id: int) -> list[str]:
    """Get all FCM tokens for a user (uses connection pool).

    Havuz RealDictCursor döndürür (satır = dict); eski `row[0]` erişimi KeyError
    veriyor ve token'ı olan HER kullanıcıda push sessizce başarısız oluyordu.
    """
    from app.core.database import _get_pool
    pool = _get_pool()
    conn = pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT fcm_token FROM fcm_tokens WHERE user_id = %s", (user_id,))
        tokens = []
        for row in cur.fetchall() or []:
            tok = row["fcm_token"] if hasattr(row, "keys") else row[0]
            if tok:
                tokens.append(tok)
        return tokens
    finally:
        pool.putconn(conn)


def send_notification(user_id: int, title: str, body: str, data: dict = None):
    """Send push notification to all devices of a user."""
    _init_firebase()
    if not _firebase_initialized:
        return

    tokens = _get_user_tokens(user_id)
    if not tokens:
        return

    notification = messaging.Notification(title=title, body=body)

    for token in tokens:
        try:
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
            )
            messaging.send(message)
        except messaging.UnregisteredError:
            # Token is invalid, clean up
            _remove_token(token)
        except Exception as e:
            print(f'[FCM] Send error: {e}')


def _remove_token(token: str):
    """Remove invalid (unregistered) token from DB — havuz bağlantısıyla.

    Eski sürüm get_db() generator'ını bağlantı sanıyordu (AttributeError).
    """
    from app.core.database import _get_pool
    pool = _get_pool()
    conn = pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM fcm_tokens WHERE fcm_token = %s", (token,))
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f'[FCM] token cleanup error: {e}')
    finally:
        pool.putconn(conn)


# ─── Convenience functions for specific notification types ───

def notify_program_assigned(client_user_id: int, program_type: str = "workout"):
    """Notify client that a new program was assigned."""
    titles = {
        "workout": "Yeni Antrenman Programı",
        "nutrition": "Yeni Beslenme Programı",
        "cardio": "Yeni Kardiyo Programı",
    }
    bodies = {
        "workout": "Koçunuz yeni bir antrenman programı hazırladı!",
        "nutrition": "Koçunuz yeni bir beslenme programı hazırladı!",
        "cardio": "Koçunuz yeni bir kardiyo programı hazırladı!",
    }
    send_notification(
        client_user_id,
        titles.get(program_type, "Yeni Program"),
        bodies.get(program_type, "Koçunuz yeni bir program hazırladı!"),
        {"type": "program_assigned", "program_type": program_type},
    )


def notify_program_updated(client_user_id: int, program_type: str = "workout"):
    """Notify client that their program was updated."""
    send_notification(
        client_user_id,
        "Program Güncellendi",
        f"{'Antrenman' if program_type == 'workout' else 'Beslenme'} programınız güncellendi.",
        {"type": "program_updated", "program_type": program_type},
    )


def notify_new_message(client_user_id: int, coach_name: str, preview: str):
    """[DEPRECATED] Geriye uyumluluk icin tutuluyor — yeni kod notify_message_to() kullanmali."""
    notify_message_to(client_user_id, coach_name, preview)


def notify_message_to(recipient_user_id: int, sender_name: str, preview: str, conversation_id: int = None):
    """Tarafsiz mesaj push'u — koc → ogrenci ya da ogrenci → koc, ikisi de ayni fonksiyon.

    title: gonderenin adi
    body:  mesaj on izlemesi (100 karakter)
    data:  type=new_message, conversation_id (varsa) — Flutter app navigate ederken kullanir
    """
    body = preview[:100] if preview else "Yeni bir mesajınız var"
    payload = {"type": "new_message"}
    if conversation_id is not None:
        payload["conversation_id"] = str(conversation_id)
    send_notification(
        recipient_user_id,
        sender_name or "Yeni mesaj",
        body,
        payload,
    )
