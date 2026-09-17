-- 068: Gerçek koç bekleme listesi ("Gerçek koçlar yakında — haber ver"). Talep ölçümü + lansman e-postası için.
CREATE TABLE IF NOT EXISTS coach_waitlist (
    user_id    INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    source     TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
