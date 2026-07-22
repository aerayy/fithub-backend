-- 053: Onboarding kolonlarını genişlet — dar VARCHAR / NUMERIC taşması 500'e yol açıyordu
--
-- KÖK NEDEN (cihaz testinde "Bir hata oluştu"):
--   POST /client/onboarding, bazı GEÇERLİ onboarding girdilerinde ham HTTP 500 dönüyordu:
--     • gender = 'Belirtmek istemiyorum' (21 karakter)  -> dar VARCHAR taşması  ← gerçek tetikleyici
--     • weight_kg / target_weight_kg >= 1000            -> NUMERIC(5,2) taşması (latent)
--     • your_goal çok uzun (40+ kr)                     -> dar VARCHAR (latent; gerçek değerler kısa)
--   Endpoint'te try/except yoktu; psycopg2 hatası ham 500 olup Flutter'da "Bir hata oluştu" gösteriyordu.
--
-- ÇÖZÜM: kategorik alanları TEXT'e (limitsiz), kilo alanlarını NUMERIC(7,2)'ye çevir.
-- ALTER ... TYPE TEXT / geniş NUMERIC güvenlidir ve tekrar çalıştırılabilir (no-op).

BEGIN;

-- client_onboarding: kategorik alanlar -> TEXT
ALTER TABLE client_onboarding ALTER COLUMN gender              TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN your_goal           TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN body_type           TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN experience          TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN how_fit             TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN knee_pain           TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN pushups             TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN stressed            TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN "commit"            TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN pref_workout_length TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN how_motivated       TYPE TEXT;
ALTER TABLE client_onboarding ALTER COLUMN plan_reference      TYPE TEXT;

-- client_onboarding: kilo alanları -> NUMERIC(7,2) (maks 99999.99, herhangi bir insan kilosu sığar)
ALTER TABLE client_onboarding ALTER COLUMN weight_kg        TYPE NUMERIC(7,2);
ALTER TABLE client_onboarding ALTER COLUMN target_weight_kg TYPE NUMERIC(7,2);

-- clients: onboarding.py bu alanları client_onboarding'den sync ediyor -> onları da genişlet
ALTER TABLE clients ALTER COLUMN gender    TYPE TEXT;
ALTER TABLE clients ALTER COLUMN goal_type TYPE TEXT;
ALTER TABLE clients ALTER COLUMN weight_kg TYPE NUMERIC(7,2);

COMMIT;
