-- Migration: Add day_payload JSONB column to workout_days table
-- This allows storing structured workout day data (title, kcal, coach_note, warmup, blocks)
-- while maintaining backward compatibility with existing workout_exercises rows

ALTER TABLE workout_days 
ADD COLUMN IF NOT EXISTS day_payload jsonb;

-- Add comment for documentation
COMMENT ON COLUMN workout_days.day_payload IS 'Structured workout day data: {title, kcal, coach_note, warmup: {duration_min, items[]}, blocks: [{title, items[]}]}';
