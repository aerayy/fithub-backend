-- Migration 040: messages.message_type CHECK constraint'ine 'voice' ekle
--
-- Sesli mesaj icin yeni message_type. media_url Cloudinary audio URL'ini tutar,
-- media_metadata icinde { duration_sec, size_bytes, mime } gibi bilgiler bulunur.

ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_message_type_check;

ALTER TABLE messages ADD CONSTRAINT messages_message_type_check
    CHECK (message_type IN ('text', 'image', 'voice'));
