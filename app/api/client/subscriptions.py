"""Client subscription management — cancel (soft/hard) + refund endpoints.

İki tip cancel:
- soft: auto_renew=false, ends_at'a kadar hizmet devam eder. Sub yenilenmez.
- hard: status=canceled hemen, programlar deaktif, koç ilişkisi kopar (clientState pasif).

Refund (15 gün içinde, started_at'tan itibaren): refund_requested_at set, status=refunded,
programlar deaktif, koç kopar. Admin onayı ile finalize edilir (POST /admin/refunds/{id}/approve).
"""
from fastapi import Depends, HTTPException, Body
from psycopg2.extras import RealDictCursor
from typing import Literal
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


class CancelRequest(BaseModel):
    type: Literal["soft", "hard"]


@router.post("/subscriptions/cancel")
def cancel_subscription(
    request: CancelRequest = Body(...),
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Aktif aboneliği iptal et.

    type='soft': "Yenilemeyi Durdur" — auto_renew=false, ends_at'a kadar hizmet devam.
    type='hard': "Aboneliği İptal Et" — status=canceled, programlar deaktif, koç kopar.
    """
    try:
        client_user_id = current_user["id"]
        cur = db.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT id, status, ends_at, started_at
            FROM subscriptions
            WHERE client_user_id = %s
              AND status IN ('active', 'pending')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (client_user_id,),
        )
        sub = cur.fetchone()
        if not sub:
            raise HTTPException(status_code=404, detail="Aktif abonelik bulunamadı")

        sub_id = sub["id"]

        if request.type == "soft":
            # Yenilemeyi Durdur: status active kalır, sadece auto_renew=false
            cur.execute(
                """UPDATE subscriptions
                   SET auto_renew = FALSE,
                       canceled_at = NOW(),
                       cancel_type = 'soft',
                       updated_at = NOW()
                   WHERE id = %s""",
                (sub_id,),
            )
            db.commit()
            return {
                "ok": True,
                "type": "soft",
                "message": "Aboneliğin sona erdiğinde otomatik yenilenmeyecek. Mevcut paketini sonuna kadar kullanabilirsin.",
                "ends_at": sub["ends_at"].isoformat() if sub["ends_at"] else None,
            }

        # Hard cancel: anında kes
        cur.execute(
            """UPDATE subscriptions
               SET status = 'canceled',
                   auto_renew = FALSE,
                   canceled_at = NOW(),
                   cancel_type = 'hard',
                   updated_at = NOW()
               WHERE id = %s""",
            (sub_id,),
        )
        # Programları deaktif et
        cur.execute(
            "UPDATE workout_programs SET is_active = FALSE, updated_at = NOW() WHERE client_user_id = %s AND is_active = TRUE",
            (client_user_id,),
        )
        cur.execute(
            "UPDATE nutrition_programs SET is_active = FALSE, updated_at = NOW() WHERE client_user_id = %s AND is_active = TRUE",
            (client_user_id,),
        )
        cur.execute(
            "UPDATE cardio_programs SET is_active = FALSE, updated_at = NOW() WHERE client_user_id = %s AND is_active = TRUE",
            (client_user_id,),
        )
        # Koç ilişkisini kes (clientState aktif → pasif)
        cur.execute(
            "UPDATE clients SET assigned_coach_id = NULL WHERE user_id = %s",
            (client_user_id,),
        )

        db.commit()
        return {
            "ok": True,
            "type": "hard",
            "message": "Aboneliğin iptal edildi. Koçunla ilişkin sonlandırıldı, programların kaldırıldı.",
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")


@router.post("/subscriptions/refund")
def request_refund(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    İade talebi oluştur — sadece program assign'dan (started_at) itibaren 15 gün içinde.
    Admin onayı sonrası refund_processed_at set edilir, para iadesi yapılır.
    """
    try:
        client_user_id = current_user["id"]
        cur = db.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            SELECT id, status, started_at, refund_requested_at
            FROM subscriptions
            WHERE client_user_id = %s
              AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (client_user_id,),
        )
        sub = cur.fetchone()
        if not sub:
            raise HTTPException(status_code=404, detail="Aktif abonelik bulunamadı")
        if sub["refund_requested_at"]:
            raise HTTPException(status_code=409, detail="İade talebin zaten mevcut, admin onayı bekleniyor.")
        if not sub["started_at"]:
            raise HTTPException(
                status_code=400,
                detail="Aboneliğin henüz başlamadı (koçun program atamadı). İade gerekmez, doğrudan iptal edebilirsin."
            )

        # 15 gün kontrolü
        cur.execute(
            "SELECT (NOW() - %s) <= INTERVAL '15 days' AS within",
            (sub["started_at"],),
        )
        within = cur.fetchone()["within"]
        if not within:
            raise HTTPException(
                status_code=409,
                detail="İade süresi geçmiş. Aboneliğin başlangıcından itibaren 15 gün içinde iade talep edilebilir."
            )

        # Refund talep — status=refunded, programlar deaktif, koç kopar
        cur.execute(
            """UPDATE subscriptions
               SET status = 'refunded',
                   refund_requested_at = NOW(),
                   canceled_at = NOW(),
                   cancel_type = 'refund',
                   auto_renew = FALSE,
                   updated_at = NOW()
               WHERE id = %s""",
            (sub["id"],),
        )
        cur.execute(
            "UPDATE workout_programs SET is_active = FALSE, updated_at = NOW() WHERE client_user_id = %s AND is_active = TRUE",
            (client_user_id,),
        )
        cur.execute(
            "UPDATE nutrition_programs SET is_active = FALSE, updated_at = NOW() WHERE client_user_id = %s AND is_active = TRUE",
            (client_user_id,),
        )
        cur.execute(
            "UPDATE cardio_programs SET is_active = FALSE, updated_at = NOW() WHERE client_user_id = %s AND is_active = TRUE",
            (client_user_id,),
        )
        cur.execute(
            "UPDATE clients SET assigned_coach_id = NULL WHERE user_id = %s",
            (client_user_id,),
        )

        db.commit()
        return {
            "ok": True,
            "message": "İade talebin alındı. Admin onayı sonrası para iadesi yapılacak.",
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bir hata oluştu. Lütfen tekrar deneyin.")
