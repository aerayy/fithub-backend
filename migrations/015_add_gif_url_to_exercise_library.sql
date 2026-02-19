-- Add gif_url column to exercise_library for ExerciseDB animated GIFs
ALTER TABLE exercise_library ADD COLUMN IF NOT EXISTS gif_url TEXT;
