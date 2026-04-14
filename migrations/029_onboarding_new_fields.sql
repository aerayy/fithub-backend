-- New onboarding fields: health, allergies, supplements, daily schedule
-- Replaces: bad_habit, stressed, what_motivate, commit, plan_reference

ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS health_problems TEXT[] DEFAULT '{}';
ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS health_problems_other TEXT DEFAULT '';
ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS food_allergies TEXT[] DEFAULT '{}';
ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS food_allergies_other TEXT DEFAULT '';
ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS supplements TEXT[] DEFAULT '{}';
ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS wakeup_time TEXT DEFAULT '';
ALTER TABLE client_onboarding ADD COLUMN IF NOT EXISTS sleep_time TEXT DEFAULT '';
