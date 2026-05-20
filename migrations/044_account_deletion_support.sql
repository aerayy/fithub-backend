-- Migration: Account deletion (KVKK + Apple Guideline 5.1.1(v))
-- Adds soft-delete marker to users for anonymized records.

BEGIN;

-- Mark account as deleted (timestamp). After deletion, users.email is replaced
-- with a unique placeholder (deleted-{id}@deleted.local) so the user cannot log in.
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);

COMMIT;
