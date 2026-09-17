-- 066: Kütüphanedeki demo/animasyon kayıtlarını (kas bilgisi olmayan "Explore Demos",
-- "Animations 1-5", "Animation", "Chest", "Abs", "Stretching") istemci araması,
-- alternatif önerileri, koç eşleştirmesi ve üretim havuzundan gizle.
-- Kayıtlar silinmez; eski programlardaki id referansları (detay by id) çalışmaya devam eder.
ALTER TABLE exercise_library ADD COLUMN IF NOT EXISTS is_hidden BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_exercise_library_hidden ON exercise_library (is_hidden) WHERE is_hidden;
UPDATE exercise_library
   SET is_hidden = TRUE
 WHERE is_hidden = FALSE
   AND canonical_name ~* '^(explore demos|animations?( [0-9]+)?|chest|abs|stretching)$'
   AND COALESCE(array_length(primary_muscles, 1), 0) = 0;
