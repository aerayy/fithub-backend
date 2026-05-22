-- Migration 048: Workout Generator v3 — kuralcı pipeline altyapısı.
--
-- Mimari: project_workout_generator_v3.md memory'sinde tam spec.
-- 7-aşamalı pipeline (ProfileAnalyzer → SplitPlanner → VolumePlanner →
-- ExerciseSelector → SessionAssembler [LLM] → Validator → Progression).
--
-- Bu migration sadece DB altyapısı; service code Faz B-D'de yazılır.
-- v2 endpoint'i paralel kalır (shadow A/B için), bu migration v2'yi
-- BOZMAZ — sadece yeni columns + yeni tablolar ekler.

BEGIN;

-- ───────────────────────────────────────────────────────────────────────
--  exercise_library — metadata genişletmesi
--  (mevcut columns: id, external_id, canonical_name, level, equipment,
--   category, primary_muscles, secondary_muscles, instructions, gif_url,
--   image_urls, aliases — DOKUNULMUYOR)
-- ───────────────────────────────────────────────────────────────────────
ALTER TABLE exercise_library
  ADD COLUMN IF NOT EXISTS movement_pattern TEXT,
  ADD COLUMN IF NOT EXISTS fatigue_score    SMALLINT,
  ADD COLUMN IF NOT EXISTS stability        TEXT,
  ADD COLUMN IF NOT EXISTS unilateral       BOOLEAN,
  ADD COLUMN IF NOT EXISTS complexity       SMALLINT,
  ADD COLUMN IF NOT EXISTS gender_skew      TEXT,
  ADD COLUMN IF NOT EXISTS goal_tags        TEXT[],
  ADD COLUMN IF NOT EXISTS equipment_required    TEXT[],
  ADD COLUMN IF NOT EXISTS equipment_alternative TEXT[];

COMMENT ON COLUMN exercise_library.movement_pattern IS
  'Hareket deseni: horizontal_press|vertical_press|horizontal_pull|vertical_pull|squat|hinge|lunge|carry|rotation|iso_curl|iso_extension|iso_fly|iso_raise|core_anti_ext|core_anti_rot|gait';

COMMENT ON COLUMN exercise_library.fatigue_score IS
  '1-10 CNS yuku. Compound barbell agir = 9-10; izolasyon makine = 2-3.';

COMMENT ON COLUMN exercise_library.stability IS
  'free|machine|cable|bodyweight|smith. Beginner uyumu icin kullanilir.';

COMMENT ON COLUMN exercise_library.complexity IS
  '1-5 skill ceiling. Beginner cap=2, intermediate=4, advanced=5. Olympic lifts=5.';

COMMENT ON COLUMN exercise_library.gender_skew IS
  'NULL=neutral, female_favored=women glute/hip focus, male_favored=heavy upper. Soft signal.';

COMMENT ON COLUMN exercise_library.goal_tags IS
  'hypertrophy|strength|power|endurance|mobility|fat_loss — birden cok atanabilir.';

CREATE INDEX IF NOT EXISTS idx_ex_lib_movement_pattern
  ON exercise_library(movement_pattern);
CREATE INDEX IF NOT EXISTS idx_ex_lib_complexity
  ON exercise_library(complexity);
CREATE INDEX IF NOT EXISTS idx_ex_lib_gin_primary_muscles
  ON exercise_library USING GIN(primary_muscles);
CREATE INDEX IF NOT EXISTS idx_ex_lib_gin_goal_tags
  ON exercise_library USING GIN(goal_tags);
CREATE INDEX IF NOT EXISTS idx_ex_lib_gin_equipment_required
  ON exercise_library USING GIN(equipment_required);


-- ───────────────────────────────────────────────────────────────────────
--  training_profiles — ProfileAnalyzer ciktisi
--  Audit + retrieval anahtari. user_id + generation_run_id ile her
--  program uretiminde donmus snapshot saklanir.
-- ───────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS training_profiles (
  id                  SERIAL PRIMARY KEY,
  user_id             INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  goal                TEXT NOT NULL CHECK (goal IN
                        ('hypertrophy','strength','fat_loss','general','endurance','recomp')),
  experience          TEXT NOT NULL CHECK (experience IN
                        ('beginner','intermediate','advanced')),
  days_per_week       SMALLINT NOT NULL CHECK (days_per_week BETWEEN 1 AND 7),
  session_duration    SMALLINT NOT NULL,
  equipment           TEXT[] NOT NULL DEFAULT '{}',
  priority_muscles    TEXT[] NOT NULL DEFAULT '{}',
  contraindications   TEXT[] NOT NULL DEFAULT '{}',
  recommended_split   TEXT,
  gender              TEXT,
  complexity_cap      SMALLINT NOT NULL DEFAULT 5,
  source_onboarding_id INT,
  computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_profiles_user
  ON training_profiles(user_id, computed_at DESC);


-- ───────────────────────────────────────────────────────────────────────
--  split_templates — yeniden kullanılabilir split kataloğu
--  Beginner→PPL agresif atama yapılmasin diye experience_lock var.
-- ───────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS split_templates (
  id              SERIAL PRIMARY KEY,
  split_id        TEXT UNIQUE NOT NULL,
  display_name    TEXT NOT NULL,
  family          TEXT NOT NULL,           -- 'fb','ul','ppl','arnold','hybrid','specialization'
  days_per_week   SMALLINT NOT NULL,
  experience_lock TEXT[] NOT NULL DEFAULT '{}',  -- {} = any, {'beginner'} = beginner only,
                                                  -- {'intermediate','advanced'} = exclude beginner
  goal_match      TEXT[] NOT NULL DEFAULT '{}',
  day_sessions    JSONB NOT NULL,           -- [{name:'Upper A', muscles:['chest','back','shoulder','triceps','biceps']},...]
  rank            SMALLINT NOT NULL DEFAULT 100,    -- ayni filtrede onlik
  rationale       TEXT,
  active          BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_split_templates_lookup
  ON split_templates(days_per_week, active);


-- ───────────────────────────────────────────────────────────────────────
--  rag_program_patterns — BeGreens programlarindan cikarilmis YAPISAL desenler
--  RAW TEXT DEGIL — extract edilmis sayisal/kategorik signal'ler.
--  Bu desenler VolumePlanner'da bias olarak kullanilir, LLM'e gosterilmez.
-- ───────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rag_program_patterns (
  id              SERIAL PRIMARY KEY,
  source_plan_id  INT,                     -- rag_training_plans.id (nullable, ETL sonradan)
  goal            TEXT,
  experience      TEXT,
  days_per_week   SMALLINT,
  split_family    TEXT,                    -- 'fb','ul','ppl','arnold','other'
  weekly_set_distribution JSONB,           -- {'chest':16,'back':18,'side_delts':10,...}
  session_movement_template JSONB,         -- per session: [comp,comp,mid,mid,iso,iso]
  rep_scheme      TEXT,                    -- '5x5','3x10','rest_pause','heavy_light','undulating'
  popularity      SMALLINT DEFAULT 1,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_patterns_lookup
  ON rag_program_patterns(goal, experience, days_per_week);


-- ───────────────────────────────────────────────────────────────────────
--  program_microcycles — 1 program × 4 hafta progression
--  Base week (week_number=1) workout_programs'da, sonraki haftalar
--  burada delta payload olarak.
-- ───────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS program_microcycles (
  id                  SERIAL PRIMARY KEY,
  workout_program_id  INT NOT NULL REFERENCES workout_programs(id) ON DELETE CASCADE,
  week_number         SMALLINT NOT NULL CHECK (week_number BETWEEN 1 AND 8),
  delta_strategy      TEXT NOT NULL CHECK (delta_strategy IN
                        ('baseline','add_reps','add_load','add_sets','deload','rest_pause','intensity_technique')),
  delta_payload       JSONB NOT NULL DEFAULT '{}'::JSONB,
  notes               TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (workout_program_id, week_number)
);


-- ───────────────────────────────────────────────────────────────────────
--  workout_programs — v3 isaretleyici + validation score
--  v2 ile birlikte kalir; pipeline_version ile ayirt edilir.
-- ───────────────────────────────────────────────────────────────────────
ALTER TABLE workout_programs
  ADD COLUMN IF NOT EXISTS pipeline_version    TEXT DEFAULT 'v2',
  ADD COLUMN IF NOT EXISTS validation_score    SMALLINT,
  ADD COLUMN IF NOT EXISTS training_profile_id INT REFERENCES training_profiles(id);

CREATE INDEX IF NOT EXISTS idx_workout_programs_pipeline
  ON workout_programs(pipeline_version);

COMMIT;
