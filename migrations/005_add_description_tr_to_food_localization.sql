-- Migration: Add description_tr column to food_localization_tr
-- Purpose: Store Turkish description for food items (AI translated)

ALTER TABLE food_localization_tr 
ADD COLUMN IF NOT EXISTS description_tr TEXT;

COMMENT ON COLUMN food_localization_tr.description_tr IS 'Turkish description of the food item (AI translated from English)';
