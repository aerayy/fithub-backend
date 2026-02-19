CREATE TABLE IF NOT EXISTS client_recovery_cache (
  user_id INT PRIMARY KEY REFERENCES users(id),
  tips_json JSONB NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
