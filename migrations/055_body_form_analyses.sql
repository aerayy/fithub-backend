-- Migration 055: body_form_analyses — vücut form fotoğraflarının AI değerlendirmesi.
--
-- Pro/Elite "vücut form analizi" özelliği: kullanıcının son fotoğraf seti
-- (DISTINCT ON angle) gpt-4o-mini vision ile değerlendirilir, sonuç burada
-- saklanır. Kota: ai_quota_usage.body_analysis (Pro 10/ay).
-- İdempotent: tekrar koşulabilir.

BEGIN;

CREATE TABLE IF NOT EXISTS body_form_analyses (
    id              SERIAL PRIMARY KEY,
    client_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    photo_ids       INTEGER[] NOT NULL DEFAULT '{}',
    analysis        JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_body_form_analyses_client
  ON body_form_analyses (client_user_id, created_at DESC);

COMMIT;
