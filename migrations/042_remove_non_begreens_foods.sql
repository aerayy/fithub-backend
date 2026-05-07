-- Migration: Remove non-BeGreens (USDA / open-source) foods.
-- Rationale: AI nutrition generator should only use coach-curated Turkish foods.
-- food_nutrients_100g and food_localization_tr have ON DELETE CASCADE on food_id,
-- so deleting from food_items also drops their dependent rows.

BEGIN;

-- Sanity counts before delete (visible in psql output)
SELECT source, COUNT(*) AS total
FROM food_items
GROUP BY source
ORDER BY source;

DELETE FROM food_items
WHERE source IS DISTINCT FROM 'begreens';

-- Verify final state
SELECT source, COUNT(*) AS remaining
FROM food_items
GROUP BY source
ORDER BY source;

COMMIT;
