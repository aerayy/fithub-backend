-- Migration 041: konversation arşiv + mesaj arama indexi
--
-- archived_at: kullanıcı bir sohbeti arşivlerse timestamp set, eski hale dönerse NULL
-- pg_trgm extension: ILIKE search'lerini index'le hızlandırmak için trigram

CREATE EXTENSION IF NOT EXISTS pg_trgm;

ALTER TABLE conversations
  ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_conversations_archived
  ON conversations(client_user_id, archived_at) WHERE archived_at IS NOT NULL;

-- Mesaj body'lerinde ILIKE search'i hızlandırır.
-- Trigram GIN index, kismii eslesmeleri (%kelime%) bile sub-100ms cevirir.
CREATE INDEX IF NOT EXISTS idx_messages_body_trgm
  ON messages USING gin (body gin_trgm_ops);
