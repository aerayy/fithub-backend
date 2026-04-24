-- Schema drift düzeltmesi: backend kodu bu kolonları bekliyor ama migration dosyası yok.
-- Hepsi IF NOT EXISTS — prod'da varsa hiçbir şey olmaz, yoksa eklenir.

-- clients tablosu: updated_at
ALTER TABLE clients ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- client_onboarding tablosu: eksik kolonlar
ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS preferred_workout_days JSONB;
ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS preferred_workout_hours TEXT DEFAULT '';
ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS nutrition_budget TEXT DEFAULT '';
ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS target_weight_kg NUMERIC(5,2);
