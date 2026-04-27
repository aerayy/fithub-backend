-- Migration 039: KIRMIZI CIZGI — workout_exercises.exercise_library_id NOT NULL
--
-- Amac: Hicbir egzersiz, bir exercise_library satirina baglanmadan workout'a kaydedilemesin.
-- Boylece "videosuz egzersiz" durumu DB seviyesinde imkansiz olur.
--
-- ON KOSUL: scripts/heal_broken_exercises.py once calistirilmali (NULL'lari temizleyici).
-- Eger hala NULL row varsa bu migration FAIL eder.

-- 1. Once mevcut NULL'lari kontrol et — eger varsa migration durur
DO $$
DECLARE
  null_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO null_count
  FROM workout_exercises
  WHERE exercise_library_id IS NULL;

  IF null_count > 0 THEN
    RAISE EXCEPTION 'Migration 039 kosulu saglanmadi: % NULL exercise_library_id row var. Once heal_broken_exercises.py calistir.', null_count;
  END IF;
END $$;

-- 2. NOT NULL constraint ekle
ALTER TABLE workout_exercises
  ALTER COLUMN exercise_library_id SET NOT NULL;

-- 3. CHECK constraint olarak da bagla (defansif — bazi DB driver'lari NOT NULL'i atlatabilir)
ALTER TABLE workout_exercises
  ADD CONSTRAINT workout_exercises_library_id_required
  CHECK (exercise_library_id IS NOT NULL);

-- 4. Foreign key garantisi: silinen library satiri varsa SET NULL yerine RESTRICT
-- (NOT NULL constraint zaten silinmeyi de engeller ama açık olalim)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'workout_exercises_exercise_library_id_fkey'
      AND table_name = 'workout_exercises'
  ) THEN
    ALTER TABLE workout_exercises
      ADD CONSTRAINT workout_exercises_exercise_library_id_fkey
      FOREIGN KEY (exercise_library_id)
      REFERENCES exercise_library (id)
      ON DELETE RESTRICT;
  END IF;
END $$;
