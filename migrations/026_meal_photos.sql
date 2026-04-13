-- Meal photo tracking (separate from chat messages)
CREATE TABLE IF NOT EXISTS meal_photos (
    id              SERIAL PRIMARY KEY,
    client_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coach_user_id   INTEGER,
    meal_label      VARCHAR(100) NOT NULL,
    photo_url       TEXT NOT NULL,
    is_retake       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meal_photos_client
    ON meal_photos(client_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_meal_photos_coach
    ON meal_photos(coach_user_id, client_user_id, created_at DESC);
