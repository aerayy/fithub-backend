-- Body form analysis photos (front, back, left_side, right_side)
-- Retake = new INSERT; latest per angle fetched via DISTINCT ON

CREATE TABLE IF NOT EXISTS body_form_photos (
    id              SERIAL PRIMARY KEY,
    client_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coach_user_id   INTEGER,
    angle           VARCHAR(20) NOT NULL CHECK (angle IN ('front','back','left_side','right_side')),
    photo_url       TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_body_form_user
    ON body_form_photos(client_user_id, created_at DESC);
