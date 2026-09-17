-- 068: Gerçek koç bekleme listesi ("Gerçek koçlar yakında — haber ver"). Talep ölçümü + lansman e-postası için.
-- NOT: users(id) FK bilerek YOK — FK eklemek users tablosunda SHARE ROW EXCLUSIVE kilidi ister ve
-- açık (idle-in-transaction) oturumlar varken deploy'u askıda bırakabilir. user_id uygulama katmanında doğrulanır.
CREATE TABLE IF NOT EXISTS coach_waitlist (
    user_id    INTEGER PRIMARY KEY,
    source     TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
