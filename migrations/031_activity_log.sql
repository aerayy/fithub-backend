-- Activity log: tracks student actions for coach notification panel
CREATE TABLE IF NOT EXISTS activity_log (
    id              SERIAL PRIMARY KEY,
    client_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coach_user_id   INTEGER,
    action_type     VARCHAR(50) NOT NULL,  -- meal_photo, form_photo, workout_complete, message
    title           TEXT NOT NULL,
    detail          TEXT DEFAULT '',
    photo_url       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_log_coach
    ON activity_log(coach_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_activity_log_client
    ON activity_log(client_user_id, created_at DESC);
