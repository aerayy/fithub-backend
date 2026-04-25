-- Meal photo AI analysis — BETA özelliği
-- GPT-4o-mini vision API ile yemek fotoğrafından makro tahmini.
-- ai_analysis yapı:
-- {
--   "calories": 520,
--   "protein_g": 35,
--   "carbs_g": 60,
--   "fat_g": 18,
--   "items": [
--     {"name": "Izgara tavuk göğsü", "estimated_g": 150},
--     {"name": "Pilav", "estimated_g": 100}
--   ],
--   "confidence": "medium",  -- low/medium/high
--   "model": "gpt-4o-mini",
--   "analyzed_at": "2026-04-25T16:30:00Z"
-- }
-- NULL = henüz analiz edilmedi veya analiz başarısız.

ALTER TABLE meal_photos ADD COLUMN IF NOT EXISTS ai_analysis JSONB;
ALTER TABLE meal_photos ADD COLUMN IF NOT EXISTS ai_analysis_status TEXT DEFAULT 'pending';
-- pending: henüz analiz başlamadı
-- processing: API çağrısı yapılıyor
-- completed: ai_analysis dolu
-- failed: hata aldı, retry edilebilir

-- Status için CHECK
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_meal_photo_ai_status') THEN
    ALTER TABLE meal_photos
      ADD CONSTRAINT chk_meal_photo_ai_status
      CHECK (ai_analysis_status IN ('pending', 'processing', 'completed', 'failed'));
  END IF;
END$$;

-- Index pending olanları cron için (ileride retry edebiliriz)
CREATE INDEX IF NOT EXISTS idx_meal_photos_ai_pending
  ON meal_photos(created_at)
  WHERE ai_analysis_status = 'pending';
