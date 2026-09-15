-- 064: set bazlı antrenman kaydı (ağırlık × tekrar) — egzersiz geçmişi ve kişisel rekor için.
CREATE TABLE IF NOT EXISTS workout_set_logs (
  id            BIGSERIAL PRIMARY KEY,
  user_id       INTEGER NOT NULL,
  session_date  DATE NOT NULL DEFAULT CURRENT_DATE,
  day_key       TEXT,
  exercise_key  TEXT NOT NULL,          -- 'lib:<exercise_library_id>' veya 'name:<normalize ad>'
  exercise_name TEXT,
  library_id    INTEGER,
  set_index     SMALLINT NOT NULL,
  weight_kg     NUMERIC(6,2),
  reps          SMALLINT,
  rpe           NUMERIC(3,1),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_workout_set_logs UNIQUE (user_id, session_date, exercise_key, set_index)
);
CREATE INDEX IF NOT EXISTS idx_workout_set_logs_user_ex ON workout_set_logs (user_id, exercise_key, session_date DESC);
