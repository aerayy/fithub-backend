-- 024: Add referral_code column to coaches for coach referral system
-- Coaches can share their code (e.g. ERAY10) with potential students on social media

ALTER TABLE coaches ADD COLUMN IF NOT EXISTS referral_code VARCHAR(20);

-- Case-insensitive unique index: "eray10" and "ERAY10" resolve to the same coach
-- Partial index: only non-null values are indexed
CREATE UNIQUE INDEX IF NOT EXISTS idx_coaches_referral_code_upper
  ON coaches (UPPER(referral_code)) WHERE referral_code IS NOT NULL;
