-- 062: OpenAI token kullanımı kaydı (maliyet görünürlüğü)
CREATE TABLE IF NOT EXISTS ai_usage_log (
  id                BIGSERIAL PRIMARY KEY,
  user_id           INTEGER,
  feature           TEXT NOT NULL,
  model             TEXT,
  prompt_tokens     INTEGER,
  completion_tokens INTEGER,
  total_tokens      INTEGER,
  duration_ms       INTEGER,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_usage_log_created ON ai_usage_log (created_at);
CREATE INDEX IF NOT EXISTS idx_ai_usage_log_user ON ai_usage_log (user_id, created_at);
