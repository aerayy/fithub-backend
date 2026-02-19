CREATE TABLE IF NOT EXISTS client_motivation_cache (
  user_id INT PRIMARY KEY REFERENCES users(id),
  motivation_json JSONB NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS client_challenge_cache (
  user_id INT PRIMARY KEY REFERENCES users(id),
  challenge_json JSONB NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
