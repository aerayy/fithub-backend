-- 010: Add media support to messages for image messaging
-- Run this on Render PSQL before deploying backend

ALTER TABLE messages ADD COLUMN IF NOT EXISTS message_type TEXT NOT NULL DEFAULT 'text';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS media_url TEXT;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS media_metadata JSONB;

-- Allow body to be null for image-only messages
ALTER TABLE messages ALTER COLUMN body DROP NOT NULL;

-- Add check constraint for message_type
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'messages_message_type_check'
    ) THEN
        ALTER TABLE messages ADD CONSTRAINT messages_message_type_check
            CHECK (message_type IN ('text', 'image'));
    END IF;
END $$;

-- Index for filtering by type
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);
