-- Migration: Add columns for Google OAuth sign-in
-- auth_provider: 'google' | null (null = email/password)
-- provider_user_id: Google "sub" (unique per Google account)

ALTER TABLE users
ADD COLUMN IF NOT EXISTS auth_provider TEXT;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS provider_user_id TEXT;

-- Allow password_hash to be null for Google-only users
ALTER TABLE users
ALTER COLUMN password_hash DROP NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_provider
ON users (auth_provider, provider_user_id)
WHERE auth_provider = 'google' AND provider_user_id IS NOT NULL;

COMMENT ON COLUMN users.auth_provider IS 'OAuth provider: google, or null for email/password';
COMMENT ON COLUMN users.provider_user_id IS 'Provider unique user ID (e.g. Google sub)';
