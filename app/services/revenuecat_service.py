"""RevenueCat integration for AI Coach subscriptions.

RevenueCat, Google Play + Apple satın almalarını tek katmanda birleştirir.
Kendi receipt validation yazmıyoruz; RevenueCat doğrular ve bize iki yoldan
bildirir:

  1. **Webhook** (`/webhooks/revenuecat`) — sunucu-otoriter olay akışı
     (INITIAL_PURCHASE, RENEWAL, CANCELLATION, EXPIRATION, ...). Yenileme,
     iptal ve süre bitişleri buradan gelir.
  2. **REST sync** (`/ai-coach/subscription/sync`) — satın alma sonrası
     anlık, webhook yarışını önlemek için uygulamanın çağırdığı doğrulama.
     RevenueCat REST API'sinden abonenin güncel entitlement'ını okur.

Her iki yol da aynı `apply_subscription` / `mark_expired` fonksiyonlarını
kullanır, böylece `ai_subscriptions` tablosu tek gerçeklik kaynağı kalır ve
kod tabanının geri kalanı (quota guard vb.) değişmeden çalışır.

**Mimari kararı:** Tek entitlement `ai_coach`. Tier (starter/pro/elite) ve
billing_period (monthly/yearly), satın alınan **product_id**'den türetilir
(`com.fithubpoint.app.ai.{tier}.{period}`). Böylece RevenueCat tarafı minimal
kalır ve tier→kota mantığı backend'de tek yerde durur (bkz.
ai_subscription_service.TIER_LIMITS).

Env:
  REVENUECAT_SECRET_API_KEY  — v1 secret key (REST sync için; sk_...)
  REVENUECAT_WEBHOOK_AUTH    — webhook Authorization header shared secret
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Tek entitlement — RevenueCat dashboard'da bu id ile tanımlanmalı.
ENTITLEMENT_ID = "ai_coach"

REVENUECAT_API_BASE = "https://api.revenuecat.com/v1"

VALID_TIERS = ("starter", "pro", "elite")

# Bilinen product id'ler için kesin eşleme (parse_product_id fallback'inden önce gelir).
PRODUCT_TIER_MAP: dict[str, tuple[str, str]] = {
    "com.fithubpoint.app.ai.starter.monthly": ("starter", "monthly"),
    "com.fithubpoint.app.ai.starter.yearly": ("starter", "yearly"),
    "com.fithubpoint.app.ai.pro.monthly": ("pro", "monthly"),
    "com.fithubpoint.app.ai.pro.yearly": ("pro", "yearly"),
    "com.fithubpoint.app.ai.elite.monthly": ("elite", "monthly"),
    "com.fithubpoint.app.ai.elite.yearly": ("elite", "yearly"),
}


# ──────────────────────────────────────────────────────────────────────
#  Parsing helpers
# ──────────────────────────────────────────────────────────────────────
def parse_product_id(product_id: Optional[str]) -> tuple[Optional[str], str]:
    """product_id → (tier, billing_period). Bilinmeyen tier → (None, ...).

    Google Play base plan id'leri product'a ':' ile eklenebilir
    (com.fithubpoint.app.ai.pro.monthly:monthly-plan) — bu yüzden hem tam
    eşleme hem de gevşek anahtar-kelime eşlemesi yapıyoruz.
    """
    if not product_id:
        return (None, "monthly")

    base = product_id.split(":", 1)[0]  # Play base-plan suffix'ini at
    if base in PRODUCT_TIER_MAP:
        return PRODUCT_TIER_MAP[base]
    if product_id in PRODUCT_TIER_MAP:
        return PRODUCT_TIER_MAP[product_id]

    p = product_id.lower()
    tier = next((t for t in VALID_TIERS if t in p), None)
    period = "yearly" if ("year" in p or "annual" in p or "annually" in p) else "monthly"
    return (tier, period)


def _to_int_user_id(app_user_id, aliases=None) -> Optional[int]:
    """RevenueCat app_user_id → bizim int user id. Anonim ($RCAnonymousID) veya
    sayısal olmayan id'lerde None döner (o event atlanır)."""
    for candidate in [app_user_id] + list(aliases or []):
        if candidate is None:
            continue
        s = str(candidate).strip()
        if s.isdigit():
            try:
                return int(s)
            except ValueError:
                continue
    return None


def _ms_to_dt(ms) -> Optional[datetime]:
    if ms is None:
        return None
    try:
        return datetime.fromtimestamp(int(ms) / 1000.0, tz=timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def _iso_to_dt(s) -> Optional[datetime]:
    if not s:
        return None
    try:
        # RevenueCat ISO: '2026-08-01T12:00:00Z'
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _norm_store(store) -> Optional[str]:
    if not store:
        return None
    s = str(store).lower()
    if "play" in s or s == "google":
        return "play_store"
    if "app_store" in s or "apple" in s or s == "ios":
        return "app_store"
    return s


def _default_expiry(billing_period: str) -> datetime:
    days = 365 if billing_period == "yearly" else 30
    return datetime.now(timezone.utc) + timedelta(days=days)


# ──────────────────────────────────────────────────────────────────────
#  DB writers — idempotent
# ──────────────────────────────────────────────────────────────────────
def apply_subscription(
    conn,
    user_id: int,
    tier: str,
    billing_period: str,
    *,
    product_id: Optional[str],
    expires_at: datetime,
    store: Optional[str] = None,
    store_transaction_id: Optional[str] = None,
    environment: Optional[str] = None,
    app_user_id: Optional[str] = None,
    status: str = "active",
) -> None:
    """Kullanıcının aktif AI aboneliğini oluştur/güncelle (idempotent).

    Eşleme önceliği:
      1. store_transaction_id ile eşleşen satır varsa → onu güncelle
         (yenileme/upgrade aynı satırda kalır, satır çoğalmaz).
      2. Yoksa kullanıcının mevcut active/mock satırı varsa → onu güncelle
         (REST sync + webhook aynı satırı yakalar, çift kayıt olmaz).
      3. Hiçbiri yoksa → yeni satır ekle.

    Tek anda tek aktif abonelik garantisi korunur.
    """
    if tier not in VALID_TIERS:
        raise ValueError(f"invalid tier: {tier}")
    if billing_period not in ("monthly", "yearly"):
        billing_period = "monthly"

    cur = conn.cursor(cursor_factory=RealDictCursor)

    target_id = None
    if store_transaction_id:
        cur.execute(
            "SELECT id FROM ai_subscriptions WHERE store_transaction_id = %s ORDER BY id DESC LIMIT 1",
            (store_transaction_id,),
        )
        row = cur.fetchone()
        if row:
            target_id = row["id"]

    if target_id is None:
        cur.execute(
            """
            SELECT id FROM ai_subscriptions
            WHERE user_id = %s AND status IN ('active', 'mock')
            ORDER BY expires_at DESC LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            target_id = row["id"]

    if target_id is not None:
        cur.execute(
            """
            UPDATE ai_subscriptions SET
                tier = %s,
                billing_period = %s,
                status = %s,
                expires_at = %s,
                product_id = COALESCE(%s, product_id),
                store = COALESCE(%s, store),
                store_transaction_id = COALESCE(%s, store_transaction_id),
                environment = COALESCE(%s, environment),
                rc_app_user_id = COALESCE(%s, rc_app_user_id),
                auto_renew = TRUE,
                canceled_at = NULL,
                updated_at = NOW()
            WHERE id = %s
            """,
            (tier, billing_period, status, expires_at, product_id, store,
             store_transaction_id, environment, app_user_id, target_id),
        )
    else:
        cur.execute(
            """
            INSERT INTO ai_subscriptions
                (user_id, tier, billing_period, status, started_at, expires_at,
                 store, product_id, store_transaction_id, environment, rc_app_user_id, auto_renew)
            VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, TRUE)
            """,
            (user_id, tier, billing_period, status, expires_at, store, product_id,
             store_transaction_id, environment, app_user_id),
        )

    conn.commit()
    logger.info(
        "ai_sub: applied user=%s tier=%s period=%s status=%s store=%s exp=%s",
        user_id, tier, billing_period, status, store, expires_at,
    )


def mark_expired(conn, user_id: int, store_transaction_id: Optional[str] = None) -> None:
    """Aboneliği 'expired' yap. mock satırlara DOKUNMAZ (dev/test korunur)."""
    cur = conn.cursor()
    if store_transaction_id:
        cur.execute(
            """
            UPDATE ai_subscriptions
            SET status = 'expired', updated_at = NOW()
            WHERE store_transaction_id = %s AND status IN ('active')
            """,
            (store_transaction_id,),
        )
    else:
        cur.execute(
            """
            UPDATE ai_subscriptions
            SET status = 'expired', updated_at = NOW()
            WHERE user_id = %s AND status = 'active'
            """,
            (user_id,),
        )
    conn.commit()


def set_auto_renew(conn, user_id: int, value: bool, store_transaction_id: Optional[str] = None) -> None:
    """auto_renew bayrağını değiştir. İptal (CANCELLATION) erişimi HEMEN
    kesmez — kullanıcı süresi bitene kadar kullanır; sadece yenileme kapanır."""
    cur = conn.cursor()
    if store_transaction_id:
        cur.execute(
            """
            UPDATE ai_subscriptions
            SET auto_renew = %s,
                canceled_at = CASE WHEN %s THEN NULL ELSE NOW() END,
                updated_at = NOW()
            WHERE store_transaction_id = %s
            """,
            (value, value, store_transaction_id),
        )
    else:
        cur.execute(
            """
            UPDATE ai_subscriptions
            SET auto_renew = %s, updated_at = NOW()
            WHERE user_id = %s AND status = 'active'
            """,
            (value, user_id),
        )
    conn.commit()


# ──────────────────────────────────────────────────────────────────────
#  Webhook event handler
# ──────────────────────────────────────────────────────────────────────
# Satın alma / yenileme / erişim kazandıran olaylar
_GRANT_EVENTS = {
    "INITIAL_PURCHASE",
    "RENEWAL",
    "PRODUCT_CHANGE",
    "UNCANCELLATION",
    "NON_RENEWING_PURCHASE",
}


def handle_webhook_event(conn, event: dict) -> dict:
    """RevenueCat webhook event'ini işle. Dönüş: özet dict (log/response için).

    İşlenemeyen ama HATA olmayan durumlar (anonim user, bilinmeyen product,
    ilgisiz event) 'skipped'/'ignored' döner → webhook 200 alır, RC retry
    yapmaz. Beklenmeyen (DB) hatalar YUKARI fırlar → webhook 500 → RC retry.
    """
    etype = (event or {}).get("type", "")
    app_user_id = event.get("app_user_id") or event.get("original_app_user_id")
    user_id = _to_int_user_id(app_user_id, event.get("aliases"))
    if user_id is None:
        return {"skipped": "no_numeric_user_id", "type": etype, "app_user_id": app_user_id}

    product_id = event.get("product_id")
    store = _norm_store(event.get("store"))
    environment = (event.get("environment") or "").lower() or None
    txn = event.get("original_transaction_id") or event.get("transaction_id")

    if etype in _GRANT_EVENTS:
        tier, period = parse_product_id(product_id)
        if not tier:
            logger.warning("revenuecat: unmapped product_id=%s type=%s", product_id, etype)
            return {"skipped": "unmapped_product", "product_id": product_id, "type": etype}
        expires_at = _ms_to_dt(event.get("expiration_at_ms")) or _default_expiry(period)
        apply_subscription(
            conn, user_id, tier, period,
            product_id=product_id, expires_at=expires_at, store=store,
            store_transaction_id=txn, environment=environment,
            app_user_id=str(app_user_id) if app_user_id is not None else None,
            status="active",
        )
        return {"ok": etype, "user_id": user_id, "tier": tier, "period": period}

    if etype == "CANCELLATION":
        # Kullanıcı yenilemeyi kapattı — erişim süre sonuna kadar sürer.
        set_auto_renew(conn, user_id, False, txn)
        return {"ok": "cancellation_autorenew_off", "user_id": user_id}

    if etype == "EXPIRATION":
        mark_expired(conn, user_id, txn)
        return {"ok": "expired", "user_id": user_id}

    if etype in ("BILLING_ISSUE", "SUBSCRIPTION_PAUSED"):
        # Grace period — RevenueCat entitlement'ı hâlâ aktif tutabilir; satırı
        # bozmuyoruz, süre bitişini EXPIRATION event'i getirir.
        logger.info("revenuecat: %s user=%s (no-op, grace)", etype, user_id)
        return {"ok": "noop", "type": etype, "user_id": user_id}

    # TRANSFER, SUBSCRIBER_ALIAS, TEST, INVOICE_ISSUANCE, vb.
    logger.info("revenuecat: ignored event type=%s user=%s", etype, user_id)
    return {"ok": "ignored", "type": etype, "user_id": user_id}


# ──────────────────────────────────────────────────────────────────────
#  REST sync (satın alma sonrası anlık doğrulama)
# ──────────────────────────────────────────────────────────────────────
def fetch_subscriber(app_user_id: str) -> dict:
    """RevenueCat REST API'sinden abonenin güncel durumunu çek.

    GET /v1/subscribers/{app_user_id} — Authorization: Bearer <SECRET_KEY>.
    """
    key = os.getenv("REVENUECAT_SECRET_API_KEY", "").strip()
    if not key:
        raise RuntimeError("REVENUECAT_SECRET_API_KEY not configured")
    resp = requests.get(
        f"{REVENUECAT_API_BASE}/subscribers/{app_user_id}",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def sync_from_subscriber(conn, user_id: int, subscriber_payload: dict) -> dict:
    """REST subscriber cevabından ai_coach entitlement'ını okuyup DB'yi güncelle.

    Aktif entitlement varsa apply_subscription; yoksa/süresi geçmişse
    mark_expired (mock'a dokunmadan)."""
    sub = (subscriber_payload or {}).get("subscriber", {}) or {}
    entitlements = sub.get("entitlements", {}) or {}
    ent = entitlements.get(ENTITLEMENT_ID)

    if not ent:
        mark_expired(conn, user_id)
        return {"active": False, "reason": "no_entitlement"}

    expires = _iso_to_dt(ent.get("expires_date"))
    now = datetime.now(timezone.utc)
    if expires is not None and expires <= now:
        mark_expired(conn, user_id)
        return {"active": False, "reason": "expired", "expires_at": ent.get("expires_date")}

    product_id = ent.get("product_identifier")
    tier, period = parse_product_id(product_id)
    if not tier:
        logger.warning("revenuecat sync: unmapped product_id=%s user=%s", product_id, user_id)
        return {"active": False, "reason": "unmapped_product", "product_id": product_id}

    # subscriptions map'ten store + environment çek
    subs_map = sub.get("subscriptions", {}) or {}
    srow = subs_map.get(product_id, {}) or {}
    store = _norm_store(srow.get("store"))
    environment = "sandbox" if srow.get("is_sandbox") else ("production" if srow else None)

    apply_subscription(
        conn, user_id, tier, period,
        product_id=product_id,
        expires_at=expires or _default_expiry(period),
        store=store,
        store_transaction_id=None,  # webhook original_transaction_id'yi sonradan doldurur
        environment=environment,
        app_user_id=str(user_id),
        status="active",
    )
    return {"active": True, "tier": tier, "period": period, "expires_at": ent.get("expires_date")}
