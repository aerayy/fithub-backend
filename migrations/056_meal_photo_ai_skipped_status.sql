-- 056: meal_photos.ai_analysis_status'a 'skipped' değeri eklenir.
-- Fit AI Koç kotası olmayan kullanıcıların öğün fotoğrafları AI analizine
-- gönderilmez; durum 'skipped' olarak işaretlenir (fotoğraf yine koça gider).
-- 038'deki CHECK kısıtı (chk_meal_photo_ai_status) yeniden tanımlanır.
BEGIN;
ALTER TABLE meal_photos DROP CONSTRAINT IF EXISTS chk_meal_photo_ai_status;
ALTER TABLE meal_photos
  ADD CONSTRAINT chk_meal_photo_ai_status
  CHECK (ai_analysis_status IN ('pending', 'processing', 'completed', 'failed', 'skipped'));
COMMIT;
