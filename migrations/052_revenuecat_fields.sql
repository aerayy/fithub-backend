-- Migration: RevenueCat linkage fields on ai_subscriptions
--
-- AI Coach abonelikleri artık RevenueCat üzerinden (Google Play + Apple)
-- yönetiliyor. Webhook (/webhooks/revenuecat) + REST sync
-- (/ai-coach/subscription/sync) gerçek satın almaları bu kolonlara yazar.
-- Mevcut mock akış (status='mock') aynen çalışmaya devam eder — bu migration
-- sadece kolon EKLER, hiçbir mevcut davranışı değiştirmez.
--
-- get_active_tier / get_subscription_status sorguları zaten
-- (status IN ('active','mock') AND expires_at > NOW()) kontrol ediyor;
-- webhook 'active' satır yazar, 'expired'/'canceled' yaptığında otomatik düşer.

BEGIN;

ALTER TABLE ai_subscriptions
    ADD COLUMN IF NOT EXISTS store                TEXT,   -- 'play_store' | 'app_store' | 'mock'
    ADD COLUMN IF NOT EXISTS product_id           TEXT,   -- store product id: com.fithubpoint.app.ai.pro.monthly
    ADD COLUMN IF NOT EXISTS store_transaction_id TEXT,   -- RC original_transaction_id (renewal boyunca sabit)
    ADD COLUMN IF NOT EXISTS environment          TEXT,   -- 'production' | 'sandbox'
    ADD COLUMN IF NOT EXISTS rc_app_user_id       TEXT;   -- RevenueCat app_user_id (bizim user id string)

-- Webhook retry'lerinde aynı transaction'ı tek satırda güncellemek için lookup index.
-- (UNIQUE değil: mock satırlarda NULL, ayrıca upgrade/downgrade geçmişi tutulabilir.)
CREATE INDEX IF NOT EXISTS idx_ai_sub_store_txn
    ON ai_subscriptions (store_transaction_id);

COMMENT ON COLUMN ai_subscriptions.store IS 'play_store | app_store | mock — satın almanın kaynağı';
COMMENT ON COLUMN ai_subscriptions.product_id IS 'store product identifier; tier + billing_period buradan türetilir';
COMMENT ON COLUMN ai_subscriptions.store_transaction_id IS 'RevenueCat original_transaction_id — renewal boyunca sabit kalan kimlik (idempotent upsert anahtarı)';
COMMENT ON COLUMN ai_subscriptions.rc_app_user_id IS 'RevenueCat app_user_id — Purchases.logIn(userId) ile set edilen bizim user id string';

COMMIT;
