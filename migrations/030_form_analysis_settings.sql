-- Coach can set form analysis frequency per student
CREATE TABLE IF NOT EXISTS form_analysis_settings (
    id              SERIAL PRIMARY KEY,
    client_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coach_user_id   INTEGER NOT NULL,
    frequency_days  INTEGER NOT NULL DEFAULT 30,  -- how often student should upload
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(client_user_id)
);

-- Add batch_id to group photos by upload session
ALTER TABLE body_form_photos ADD COLUMN IF NOT EXISTS batch_date DATE DEFAULT CURRENT_DATE;
