-- Migration 065: Program döngü sonu bildirimi (28. gün akışı).
--
-- 4 haftalık (v3 mikrosüvel) antrenman programları 28 günde biter. Döngü
-- bitmek üzereyken / bitince öğrenciye push, gerçek koça e-posta gider.
-- Bu işaret program başına BİR kez bildirilmesini sağlar (idempotent claim:
-- UPDATE ... WHERE cycle_end_notified_at IS NULL RETURNING ...).
--
-- Tetikleyiciler: saatlik cron (POST /admin/maintenance/notify-program-endings)
-- ve öğrencinin uygulamayı açması (GET /client/workouts/active, arka plan).

ALTER TABLE workout_programs
  ADD COLUMN IF NOT EXISTS cycle_end_notified_at TIMESTAMPTZ;

-- Aktif program taramaları (döngü sonu adayları, koç panosu) için kısmi indeks.
CREATE INDEX IF NOT EXISTS idx_workout_programs_active_created
  ON workout_programs (created_at)
  WHERE is_active = TRUE;
