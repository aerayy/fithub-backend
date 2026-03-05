"""
Client notifications: unread messages and recent program assignments.
"""
from fastapi import Depends

from app.core.database import get_db
from app.core.security import require_role
from .routes import router


@router.get("/notifications")
def get_client_notifications(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    client_user_id = current_user["id"]
    cur = db.cursor()

    notifications = []

    # 1. Unread messages from coach
    cur.execute("""
        SELECT m.id, m.body, m.message_type, m.created_at,
               COALESCE(u.full_name, u.email) AS coach_name
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        JOIN users u ON u.id = c.coach_user_id
        WHERE c.client_user_id = %s AND m.sender_type = 'coach' AND m.read_at IS NULL
        ORDER BY m.created_at DESC
        LIMIT 10
    """, (client_user_id,))
    for r in cur.fetchall() or []:
        notifications.append({
            "type": "message",
            "title": f"{r['coach_name']} mesaj gönderdi",
            "body": r['body'][:100] if r.get('body') else '[Foto]',
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
        })

    # 2. Recent program assignments (last 7 days)
    cur.execute("""
        SELECT 'workout' AS program_type, title, created_at
        FROM workout_programs
        WHERE client_user_id = %s AND is_active = TRUE AND created_at > NOW() - INTERVAL '7 days'
        UNION ALL
        SELECT 'cardio' AS program_type, title, created_at
        FROM cardio_programs
        WHERE client_user_id = %s AND is_active = TRUE AND created_at > NOW() - INTERVAL '7 days'
        UNION ALL
        SELECT 'nutrition' AS program_type, title, created_at
        FROM nutrition_programs
        WHERE client_user_id = %s AND is_active = TRUE AND created_at > NOW() - INTERVAL '7 days'
        ORDER BY created_at DESC
    """, (client_user_id, client_user_id, client_user_id))
    for r in cur.fetchall() or []:
        type_names = {'workout': 'Antrenman', 'cardio': 'Kardiyo', 'nutrition': 'Beslenme'}
        type_label = type_names.get(r['program_type'], 'Program')
        notifications.append({
            "type": "program",
            "title": f"Yeni {type_label} Programı",
            "body": r.get('title') or f'{type_label} programınız atandı',
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
        })

    # Sort all by created_at desc
    notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {"notifications": notifications, "unread_count": len(notifications)}
