-- Subscription lifecycle: deferred start (program assign'da başlar), soft/hard cancel, refund

-- 1) Yeni kolonlar
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS auto_renew BOOLEAN DEFAULT TRUE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS canceled_at TIMESTAMPTZ;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS cancel_type TEXT;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS refund_requested_at TIMESTAMPTZ;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS refund_processed_at TIMESTAMPTZ;

-- 2) cancel_type için CHECK constraint
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_sub_cancel_type'
  ) THEN
    ALTER TABLE subscriptions
      ADD CONSTRAINT chk_sub_cancel_type
      CHECK (cancel_type IS NULL OR cancel_type IN ('soft', 'hard', 'refund'));
  END IF;
END$$;

-- 3) started_at artık NULL olabilir (program atanana kadar)
-- Mevcut kolonun NOT NULL olup olmadığını kontrol edip drop ediyoruz
ALTER TABLE subscriptions ALTER COLUMN started_at DROP NOT NULL;

-- 4) ends_at zaten NULL olabiliyor — kontrol amaçlı
ALTER TABLE subscriptions ALTER COLUMN ends_at DROP NOT NULL;

-- 5) Indexler — cancel/refund query'leri için
CREATE INDEX IF NOT EXISTS idx_sub_pending_refunds
  ON subscriptions (refund_requested_at)
  WHERE refund_requested_at IS NOT NULL AND refund_processed_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_sub_auto_renew_off
  ON subscriptions (client_user_id, ends_at)
  WHERE auto_renew = FALSE AND status = 'active';

-- Not: status alanı zaten 'refunded' değerini kabul ediyor olmalı.
-- Eğer CHECK constraint varsa onu da güncellemek gerekir.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'subscriptions_status_check'
  ) THEN
    -- Mevcut constraint'i drop edip yenisini ekle
    ALTER TABLE subscriptions DROP CONSTRAINT subscriptions_status_check;
  END IF;
END$$;

-- Yeni status constraint (refunded dahil)
ALTER TABLE subscriptions
  ADD CONSTRAINT subscriptions_status_check
  CHECK (status IN ('pending', 'active', 'canceled', 'expired', 'refunded'));
