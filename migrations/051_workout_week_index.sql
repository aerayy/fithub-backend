-- Migration 051: workout_days.week_index — 4-haftalık mikrosüvel için.
--
-- v3 pipeline Faz G: her satın alımda 1 program × 4 hafta üretilir.
-- workout_days satır sayısı: 4 × 7 = 28. week_index 1..4 ile filtrelenir.
--
-- Geriye uyumluluk: mevcut satırlar (v2 ve v3 phase E) week_index=1 alır.
-- Mevcut tek-hafta sorgular hala doğru çalışır (default 1 filter ya da WHERE yokken hepsi 1 dönerdi, hâlâ öyle).

BEGIN;

ALTER TABLE workout_days
  ADD COLUMN IF NOT EXISTS week_index SMALLINT NOT NULL DEFAULT 1
    CHECK (week_index BETWEEN 1 AND 4);

CREATE INDEX IF NOT EXISTS idx_workout_days_program_week_day
  ON workout_days (workout_program_id, week_index, day_of_week);

COMMENT ON COLUMN workout_days.week_index IS
  '1..4. Mikrosüvel haftası: 1=baseline, 2=add_reps, 3=add_load, 4=deload. Frontend tarih farkından (today - program.created_at) / 7 hesabı yapar.';

COMMIT;
