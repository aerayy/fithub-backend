-- Add missing profile fields to coaches table
ALTER TABLE coaches ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE coaches ADD COLUMN IF NOT EXISTS certificates TEXT[] DEFAULT ARRAY[]::TEXT[];
ALTER TABLE coaches ADD COLUMN IF NOT EXISTS photos TEXT[] DEFAULT ARRAY[]::TEXT[];
