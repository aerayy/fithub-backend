-- Migration 050: equipment_type / equipment_class / stability_requirement ayrımı.
--
-- Migration 048'de tek "stability" column'u vardı (free/machine/cable/...).
-- Bu hem **equipment class** (mekanik yapı) hem **stability requirement**
-- (biyomekanik denge ihtiyacı) anlamlarını karıştırıyordu.
--
-- Bu migration ikisini ayırır:
--
--   • equipment_type        TEXT      — primary equipment kategorisi
--                                       (selector için indexed, tek değer)
--                                       'barbell'|'dumbbell'|'cable'|'machine'|
--                                       'bodyweight'|'kettlebell'|'band'|'smith'
--
--   • equipment_class       TEXT      — eski "stability" rename;
--                                       mekanik yapı (free path vs fixed path)
--                                       'free'|'machine'|'cable'|'bodyweight'|
--                                       'smith'|'band'
--
--   • equipment_required[]  TEXT[]    — detay equipment list (mevcut, kalır)
--
--   • stability_requirement SMALLINT  — 1-5 biyomekanik denge ihtiyacı:
--                                       1 = very_low  (leg press, smith)
--                                       2 = low       (cable row, machine)
--                                       3 = medium    (bilateral barbell)
--                                       4 = high      (unilateral / free dumbbell)
--                                       5 = very_high (Olympic lifts, single-leg)
--
-- Selector logic'i:
--   profile.equipment_kategorileri WHERE equipment_type IN (...)
--   profile.injury_risk filter WHERE stability_requirement <= cap
-- iki ayrı filter çalıştırabilir.
--
-- Veri durumu: classify_exercises.py henuz tek row dahi yazmadi (sadece
-- dry-run yapildi). Bu yuzden rename + ekleme guvenli, hiç data kaybi yok.

BEGIN;

-- Eski "stability" → "equipment_class" rename
ALTER TABLE exercise_library RENAME COLUMN stability TO equipment_class;

-- Yeni columns
ALTER TABLE exercise_library
  ADD COLUMN IF NOT EXISTS equipment_type        TEXT,
  ADD COLUMN IF NOT EXISTS stability_requirement SMALLINT;

COMMENT ON COLUMN exercise_library.equipment_type IS
  'Primary equipment kategorisi (single value, indexed): barbell|dumbbell|cable|machine|bodyweight|kettlebell|band|smith. ExerciseSelector profile.equipment array ile direct lookup yapar.';

COMMENT ON COLUMN exercise_library.equipment_class IS
  '(eski stability) Mekanik yapi: free path vs fixed path. free|machine|cable|bodyweight|smith|band. Equipment kategorisinden farkli — Smith machine equipment_type=smith ama equipment_class=smith (fixed path).';

COMMENT ON COLUMN exercise_library.stability_requirement IS
  '1-5 biyomekanik denge ihtiyaci. 1=very_low (leg press), 5=very_high (snatch, pistol squat). Beginner cap 2-3, intermediate 4, advanced 5.';

CREATE INDEX IF NOT EXISTS idx_ex_lib_equipment_type
  ON exercise_library(equipment_type);
CREATE INDEX IF NOT EXISTS idx_ex_lib_stability_req
  ON exercise_library(stability_requirement);

COMMIT;
