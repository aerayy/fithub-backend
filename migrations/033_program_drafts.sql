-- Program drafts: coaches can save up to 3 draft programs per student
-- before assigning one as the active program.
-- Idempotent: CREATE TABLE IF NOT EXISTS

CREATE TABLE IF NOT EXISTS workout_program_drafts (
    id              SERIAL PRIMARY KEY,
    coach_user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL DEFAULT 'Taslak',
    payload         JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workout_drafts_coach_client
    ON workout_program_drafts(coach_user_id, client_user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS nutrition_program_drafts (
    id              SERIAL PRIMARY KEY,
    coach_user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL DEFAULT 'Taslak',
    payload         JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nutrition_drafts_coach_client
    ON nutrition_program_drafts(coach_user_id, client_user_id, created_at DESC);
