-- 061: RevenueCat webhook olay tekrar koruması (event.id bazlı idempotency)
CREATE TABLE IF NOT EXISTS revenuecat_events (
  event_id    TEXT PRIMARY KEY,
  event_type  TEXT,
  app_user_id TEXT,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_revenuecat_events_received ON revenuecat_events (received_at);
