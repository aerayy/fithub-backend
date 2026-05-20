-- Migration: KVKK + Kullanim Sartlari onay kaydi
-- Kullanici signup'ta veya OAuth ilk girisinde onay vermis sayilir.

BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_terms_at TIMESTAMP;
COMMENT ON COLUMN users.accepted_terms_at IS 'KVKK aydinlatma + kullanim sartlari kabul zamani. NULL ise kullanici henuz kabul etmemis (eski kayit veya signup yarida kalmis).';

COMMIT;
