-- Migration: Health disclaimer acceptance log
-- Apple Review Guideline 1.4.1 — fitness app sağlık disclaimer'ı in-app gösterilmeli.
-- Kullanıcının disclaimer'ı kabul ettiği an log'lanır (yasal koruma için).

BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_health_disclaimer_at TIMESTAMP;
COMMENT ON COLUMN users.accepted_health_disclaimer_at IS 'Saglik uyarisi kabul zamani. NULL ise kullanici henuz gormemis/kabul etmemis. App ilk Home acilisinda modal gosterilir.';

COMMIT;
