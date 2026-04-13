-- Track daily workout completion (which exercises were done on which day)
CREATE TABLE IF NOT EXISTS workout_sessions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    day_key         VARCHAR(10) NOT NULL,  -- 'mon','tue', etc.
    completed_ids   TEXT[] NOT NULL DEFAULT '{}',  -- array of exercise IDs marked done
    is_finished     BOOLEAN NOT NULL DEFAULT FALSE,  -- true when "Antrenmanı Bitir" tapped
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, session_date, day_key)
);

CREATE INDEX IF NOT EXISTS idx_workout_sessions_user
    ON workout_sessions(user_id, session_date DESC);
