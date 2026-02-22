-- Add social link columns to coaches table
ALTER TABLE coaches ADD COLUMN IF NOT EXISTS twitter TEXT;
ALTER TABLE coaches ADD COLUMN IF NOT EXISTS linkedin TEXT;
ALTER TABLE coaches ADD COLUMN IF NOT EXISTS website TEXT;

-- Add discount_percentage to coach_packages
ALTER TABLE coach_packages ADD COLUMN IF NOT EXISTS discount_percentage REAL DEFAULT 0;
