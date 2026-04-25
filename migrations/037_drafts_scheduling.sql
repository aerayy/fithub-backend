-- Drafts: zamanlanmış taslak özelliği
-- Koç bir tarih+saat seçtiğinde taslak otomatik olarak o anda aktive olur.

-- Workout drafts
ALTER TABLE workout_program_drafts ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ;
ALTER TABLE workout_program_drafts ADD COLUMN IF NOT EXISTS activated_at TIMESTAMPTZ;

-- Nutrition drafts
ALTER TABLE nutrition_program_drafts ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ;
ALTER TABLE nutrition_program_drafts ADD COLUMN IF NOT EXISTS activated_at TIMESTAMPTZ;

-- Cron query için partial index'ler — sadece "henüz aktive olmamış zamanlanmış" taslaklar
CREATE INDEX IF NOT EXISTS idx_workout_drafts_scheduled_pending
    ON workout_program_drafts(scheduled_at)
    WHERE scheduled_at IS NOT NULL AND activated_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_nutrition_drafts_scheduled_pending
    ON nutrition_program_drafts(scheduled_at)
    WHERE scheduled_at IS NOT NULL AND activated_at IS NULL;
