-- Migration: RAG knowledge base from BeGreens dump (16K plan, 23K profile, 518K besin).
-- Read-only reference data — generator-v2 buradan profil match yapar, asla yazmaz.
-- Production tablolari (nutrition_programs / nutrition_meals / clients) bagimsizdir.

BEGIN;

-- 1. Profiller (BeGreens users tablosundan ozetle)
CREATE TABLE IF NOT EXISTS rag_user_profiles (
    id INTEGER PRIMARY KEY,             -- BeGreens user.id
    age_text TEXT,                      -- Orjinal text, normalize edilebilir
    age_int INTEGER,                    -- Parse edilmis yas
    gender TEXT,                        -- 'male'/'female' (identity field'dan)
    height_text TEXT,                   -- Orjinal "length"
    height_cm INTEGER,                  -- Parse edilmis cm
    weight_text TEXT,
    weight_kg NUMERIC(6,2),
    fat_text TEXT,
    target INTEGER,                     -- Hedef kodu (0=?, 1=lose, 2=gain, ...)
    gym SMALLINT,                       -- 0=ev, 1=gym
    activity SMALLINT,
    sporttimes SMALLINT,                -- haftada kac antrenman
    health_problems TEXT,
    allergic TEXT,
    forbidden TEXT,
    rest_days TEXT,
    supplements TEXT,
    budget SMALLINT,
    job TEXT,
    province TEXT,
    notes TEXT,
    imported_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_profiles_target ON rag_user_profiles(target);
CREATE INDEX idx_rag_profiles_gender ON rag_user_profiles(gender);
CREATE INDEX idx_rag_profiles_gym ON rag_user_profiles(gym);
CREATE INDEX idx_rag_profiles_age ON rag_user_profiles(age_int);
CREATE INDEX idx_rag_profiles_weight ON rag_user_profiles(weight_kg);


-- 2. Beslenme planlari (16K)
CREATE TABLE IF NOT EXISTS rag_nutrition_plans (
    id INTEGER PRIMARY KEY,             -- BeGreens nutritionplans.id
    name TEXT,
    notes TEXT,                         -- HTML icerebilir
    user_id INTEGER,
    started DATE,
    ended DATE,
    edited TIMESTAMP,
    coach_personel_id TEXT,
    imported_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_nplans_user ON rag_nutrition_plans(user_id);


-- 3. Beslenme ogunleri (127K)
CREATE TABLE IF NOT EXISTS rag_nutrition_meals (
    id INTEGER PRIMARY KEY,             -- BeGreens nutrition_planmeals.id
    meal_name TEXT,                     -- "Kahvalti", "Ogle Yemegi" vs
    meal_time TIME,
    plan_id INTEGER,
    meal_note TEXT,
    imported_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_nmeals_plan ON rag_nutrition_meals(plan_id);


-- 4. Ogundeki besinler (518K) — gercek koc tarafindan secilmis
CREATE TABLE IF NOT EXISTS rag_nutrition_foods (
    id INTEGER PRIMARY KEY,             -- BeGreens nutrition_planunits.id
    name TEXT,
    quantity NUMERIC,
    weight TEXT,                        -- "100g", "1 adet", vs orjinal text
    calorie NUMERIC,
    yag NUMERIC,
    protein NUMERIC,
    karbohidrat NUMERIC,
    lif NUMERIC,
    potasyum NUMERIC,
    sodyum NUMERIC,
    meal_id INTEGER,
    imported_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_nfoods_meal ON rag_nutrition_foods(meal_id);
CREATE INDEX idx_rag_nfoods_name ON rag_nutrition_foods(name);


-- 5. Besin master DB (~500 — BeGreens'in master nutrition lookup)
CREATE TABLE IF NOT EXISTS rag_food_master (
    id INTEGER PRIMARY KEY,
    name TEXT,
    calorie NUMERIC,
    yag NUMERIC,
    protein NUMERIC,
    karbohidrat NUMERIC,
    lif NUMERIC,
    potasyum NUMERIC,
    sodyum NUMERIC,
    weight TEXT,
    notes TEXT,
    imported_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_food_master_name ON rag_food_master(name);


-- 6. Antrenman planlari (18K)
CREATE TABLE IF NOT EXISTS rag_training_plans (
    id INTEGER PRIMARY KEY,
    name TEXT,
    notes TEXT,
    user_id INTEGER,
    started DATE,
    ended DATE,
    edited TIMESTAMP,
    imported_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_tplans_user ON rag_training_plans(user_id);


-- 7. Antrenman seansi (110K)
CREATE TABLE IF NOT EXISTS rag_training_sessions (
    id INTEGER PRIMARY KEY,
    training_name TEXT,
    training_time TEXT,
    plan_id INTEGER,
    imported_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_tsessions_plan ON rag_training_sessions(plan_id);


-- 8. Egzersiz set/tekrarlari (890K) — BeGreens 3-li superset format korunuyor
CREATE TABLE IF NOT EXISTS rag_training_exercises (
    id INTEGER PRIMARY KEY,
    mid INTEGER,
    move_name TEXT,
    quantity TEXT,
    mid2 INTEGER,
    move2 TEXT,
    quantity2 TEXT,
    mid3 INTEGER,
    move3 TEXT,
    quantity3 TEXT,
    info TEXT,
    training_id INTEGER,
    notes TEXT,
    imported_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_texercises_training ON rag_training_exercises(training_id);


-- 9. Egzersiz master DB
CREATE TABLE IF NOT EXISTS rag_exercise_master (
    id INTEGER PRIMARY KEY,
    name TEXT,
    video TEXT,
    notes TEXT,
    imported_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_exercise_master_name ON rag_exercise_master(name);


COMMIT;
