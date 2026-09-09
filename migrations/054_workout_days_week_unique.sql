-- Migration 054: workout_days teklik kısıtına week_index dahil edilir.
--
-- Migration 051 week_index kolonunu ekledi ama UNIQUE (workout_program_id,
-- day_of_week) kısıtını güncellemedi. Sonuç: v3 mikrosüvel (4 hafta × 7 gün,
-- 28 satır) yazımı 2. haftanın ilk gününde UniqueViolation ile patlıyordu —
-- AI Koç satın alma akışındaki "duplicate key ... (68, mon)" hatasının kökü.
--
-- Yeni kısıt: (program, hafta, gün) üçlüsü tekil. v2 tek-hafta yazımları
-- week_index=1 default'uyla aynı teklik güvencesini korur.
-- İdempotent: tekrar koşulabilir.

BEGIN;

ALTER TABLE workout_days
  DROP CONSTRAINT IF EXISTS workout_days_workout_program_id_day_of_week_key;

-- Prod'da aynı ad CONSTRAINT değil bağımsız UNIQUE INDEX olarak yaşıyordu
-- (tablo elle kurulmuş); DROP CONSTRAINT onu düşürmez. İkisini de kapsa.
DROP INDEX IF EXISTS workout_days_workout_program_id_day_of_week_key;

ALTER TABLE workout_days
  DROP CONSTRAINT IF EXISTS workout_days_program_week_day_key;

ALTER TABLE workout_days
  ADD CONSTRAINT workout_days_program_week_day_key
    UNIQUE (workout_program_id, week_index, day_of_week);

COMMIT;
