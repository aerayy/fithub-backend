-- Migration: AI Coach tier subscriptions + monthly quota usage
--
-- 3 tier sistem (starter/pro/elite). Mevcut `subscriptions` tablosu gerçek koç
-- abonelikleri için kullanılıyor (client_user_id + coach_user_id), bunu
-- karıştırmamak için ayrı tablo `ai_subscriptions` açıyoruz.
--
-- Apple IAP DUNS sonrası gerçek satın alımla bağlanacak; şimdilik mock mode'da
-- `status='mock'` ile geliştirme/test amaçlı subscription oluşturulabilir.

BEGIN;

-- ──────────────────────────────────────────────────────────────────────
--  ai_subscriptions: kullanıcının aktif AI Coach tier'ı
-- ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_subscriptions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier            TEXT NOT NULL CHECK (tier IN ('starter', 'pro', 'elite')),
    billing_period  TEXT NOT NULL CHECK (billing_period IN ('monthly', 'yearly')),
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'expired', 'canceled', 'mock')),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL,
    apple_transaction_id TEXT,
    auto_renew      BOOLEAN DEFAULT TRUE,
    canceled_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_sub_user_active
    ON ai_subscriptions (user_id, status, expires_at DESC);

COMMENT ON TABLE ai_subscriptions IS 'AI Coach tier subscription (Starter/Pro/Elite). Mock mode supported until Apple IAP DUNS verification.';
COMMENT ON COLUMN ai_subscriptions.status IS 'active = paid/IAP, mock = dev/test (no real charge), expired = ends_at gecti, canceled = user iptal etti';

-- ──────────────────────────────────────────────────────────────────────
--  ai_quota_usage: aylik AI feature kullanım sayaçları
-- ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_quota_usage (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    month_key    TEXT NOT NULL,  -- 'YYYY-MM' format
    quota_type   TEXT NOT NULL
                 CHECK (quota_type IN ('chat', 'meal_analysis', 'body_analysis', 'workout_regen')),
    used_count   INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, month_key, quota_type)
);

CREATE INDEX IF NOT EXISTS idx_ai_quota_lookup
    ON ai_quota_usage (user_id, month_key);

COMMENT ON TABLE ai_quota_usage IS 'Per-user, per-month AI feature usage counters. Reset implicit when month_key rolls over.';
COMMENT ON COLUMN ai_quota_usage.month_key IS 'YYYY-MM format (e.g. 2026-05). Used as bucket key.';

COMMIT;
