-- 057: Rate limit sayaçları (auth endpoint'leri). Süreç içi sayaç çoklu
-- worker'da tutarsız kaldığı için (her worker kendi sayacı) DB'de sabit
-- pencere sayacı tutulur. Tablo yoksa kod bellek yedeğine düşer.
BEGIN;
CREATE TABLE IF NOT EXISTS rate_limit_buckets (
  key          TEXT PRIMARY KEY,
  window_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  count        INTEGER NOT NULL DEFAULT 0
);
COMMIT;
