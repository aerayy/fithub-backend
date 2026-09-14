-- 059: Kalıcı oturum (refresh token) kolonları. Prod'da remember_token
-- kolonları elle eklenmişti (migration yoktu); lokal/staging'de eksikti.
-- IF NOT EXISTS ile her ortamda güvenli. Hash'e göre arama için index.
BEGIN;
ALTER TABLE users ADD COLUMN IF NOT EXISTS remember_token TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS remember_token_expires_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_users_remember_token ON users (remember_token) WHERE remember_token IS NOT NULL;
COMMIT;
