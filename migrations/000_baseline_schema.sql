-- 000_baseline_schema.sql — BAŞLANGIÇ ŞEMASI (15 Eyl 2026, scripts/gen_baseline_schema.py ile üretildi)
-- Neden: users/clients/coaches/... tabloları hiçbir migration dosyasında yoktu (elle kurulmuştu);
-- boş bir veritabanına 001'den itibaren kurulum imkânsızdı (staging + CI DB testleri).
-- Sonraki migration'ların eklediği kolon/indeks/kısıtlar burada YOK, zincir onları ekler.
-- Çalıştırıcı kuralı (app/core/migrations.py): "000_" önekli dosyalar YALNIZCA users tablosu yoksa çalışır;
-- kurulu DB'de (prod/lokal) çalıştırılmadan 'uygulandı' olarak kaydedilir.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255),
    full_name character varying(255),
    role character varying(20) NOT NULL,
    timezone character varying(50) DEFAULT 'Europe/Istanbul'::character varying,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now(),
    phone_number character varying,
    phone character varying(20),
    phone_verified boolean DEFAULT false,
    email_verified boolean DEFAULT false,
    email_verification_token text,
    email_verification_expires_at timestamp without time zone,
    otp_code text,
    otp_expires_at timestamp without time zone,
    otp_attempts integer DEFAULT 0,
    otp_locked_until timestamp without time zone,
    birthdate date,
    CONSTRAINT users_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS clients (
    user_id integer NOT NULL,
    gender character varying(10),
    date_of_birth date,
    height_cm numeric(5,2),
    weight_kg numeric(5,2),
    goal_type character varying(30),
    activity_level character varying(20),
    onboarding_done boolean DEFAULT false,
    assigned_coach_id integer,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    CONSTRAINT clients_pkey PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS coaches (
    user_id integer NOT NULL,
    bio text,
    photo_url text,
    price_per_month numeric(10,2),
    rating numeric(3,2),
    rating_count integer DEFAULT 0,
    specialties text[],
    instagram character varying(255),
    is_active boolean DEFAULT true,
    full_name character varying(100),
    CONSTRAINT coaches_pkey PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS client_onboarding (
    id SERIAL NOT NULL,
    user_id integer NOT NULL,
    full_name character varying(100),
    age integer,
    weight_kg numeric(5,2),
    height_cm integer,
    gender character varying(50),
    your_goal character varying(50),
    body_type character varying(50),
    experience character varying(50),
    how_fit character varying(50),
    knee_pain character varying(50),
    pushups character varying(50),
    stressed character varying(50),
    commit character varying(50),
    pref_workout_length character varying(50),
    how_motivated character varying(50),
    plan_reference character varying(50),
    body_part_focus jsonb,
    bad_habit jsonb,
    what_motivate jsonb,
    workout_place jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT client_onboarding_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS coach_packages (
    id BIGSERIAL NOT NULL,
    coach_user_id bigint NOT NULL,
    name text NOT NULL,
    description text,
    duration_days integer NOT NULL,
    price numeric(10,2) NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    image_url text,
    CONSTRAINT coach_packages_duration_days_check CHECK ((duration_days > 0)),
    CONSTRAINT coach_packages_price_check CHECK ((price >= (0)::numeric)),
    CONSTRAINT coach_packages_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS exercise_library (
    id SERIAL NOT NULL,
    external_id character varying(150) NOT NULL,
    canonical_name character varying(150) NOT NULL,
    level character varying(50),
    equipment character varying(100),
    category character varying(100),
    primary_muscles text[],
    secondary_muscles text[],
    instructions text[],
    image_urls text[],
    created_at timestamp without time zone DEFAULT now(),
    aliases text[],
    tips text[],
    instructions_tr text[],
    tips_tr text[],
    stability text,
    CONSTRAINT exercise_library_pkey PRIMARY KEY (id),
    CONSTRAINT exercise_library_external_id_key UNIQUE (external_id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL NOT NULL,
    client_user_id integer NOT NULL,
    coach_user_id integer NOT NULL,
    plan_name text NOT NULL,
    status text NOT NULL DEFAULT 'active'::text,
    started_at timestamp without time zone,
    ends_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now(),
    purchased_at timestamp without time zone NOT NULL DEFAULT now(),
    decided_at timestamp without time zone,
    decision text,
    package_id integer,
    subscription_ref text NOT NULL,
    program_assigned_at timestamp without time zone,
    program_state text NOT NULL DEFAULT 'preparing'::text,
    CONSTRAINT chk_sub_program_state CHECK ((program_state = ANY (ARRAY['preparing'::text, 'assigned'::text]))),
    CONSTRAINT chk_sub_status CHECK ((status = ANY (ARRAY['active'::text, 'expired'::text, 'canceled'::text]))),
    CONSTRAINT subscriptions_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS workout_programs (
    id SERIAL NOT NULL,
    client_user_id integer NOT NULL,
    coach_user_id integer,
    title text,
    week_number integer,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT workout_programs_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS workout_days (
    id SERIAL NOT NULL,
    workout_program_id integer NOT NULL,
    day_of_week character varying(10) NOT NULL,
    order_index integer NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT workout_days_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS workout_exercises (
    id SERIAL NOT NULL,
    workout_day_id integer NOT NULL,
    exercise_name text NOT NULL,
    sets integer,
    reps text,
    notes text,
    order_index integer NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    exercise_library_id integer NOT NULL,
    CONSTRAINT workout_exercises_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS nutrition_programs (
    id SERIAL NOT NULL,
    client_user_id integer NOT NULL,
    coach_user_id integer,
    title text NOT NULL DEFAULT 'Nutrition Program'::text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    supplements jsonb DEFAULT '[]'::jsonb,
    CONSTRAINT nutrition_programs_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS nutrition_meals (
    id SERIAL NOT NULL,
    nutrition_program_id integer NOT NULL,
    meal_type text NOT NULL,
    content text,
    order_index integer NOT NULL DEFAULT 0,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    planned_time time without time zone,
    CONSTRAINT nutrition_meals_pkey PRIMARY KEY (id)
);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'clients_assigned_coach_id_fkey') THEN
    EXECUTE 'ALTER TABLE clients ADD CONSTRAINT clients_assigned_coach_id_fkey FOREIGN KEY (assigned_coach_id) REFERENCES coaches(user_id)';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'clients_user_id_fkey') THEN
    EXECUTE 'ALTER TABLE clients ADD CONSTRAINT clients_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'coaches_user_id_fkey') THEN
    EXECUTE 'ALTER TABLE coaches ADD CONSTRAINT coaches_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'client_onboarding_user_id_fkey') THEN
    EXECUTE 'ALTER TABLE client_onboarding ADD CONSTRAINT client_onboarding_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'coach_packages_coach_user_id_fkey') THEN
    EXECUTE 'ALTER TABLE coach_packages ADD CONSTRAINT coach_packages_coach_user_id_fkey FOREIGN KEY (coach_user_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'subscriptions_client_user_id_fkey') THEN
    EXECUTE 'ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_client_user_id_fkey FOREIGN KEY (client_user_id) REFERENCES users(id)';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'subscriptions_coach_user_id_fkey') THEN
    EXECUTE 'ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_coach_user_id_fkey FOREIGN KEY (coach_user_id) REFERENCES users(id)';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'subscriptions_package_id_fkey') THEN
    EXECUTE 'ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_package_id_fkey FOREIGN KEY (package_id) REFERENCES coach_packages(id)';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'workout_programs_client_user_id_fkey') THEN
    EXECUTE 'ALTER TABLE workout_programs ADD CONSTRAINT workout_programs_client_user_id_fkey FOREIGN KEY (client_user_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'workout_programs_coach_user_id_fkey') THEN
    EXECUTE 'ALTER TABLE workout_programs ADD CONSTRAINT workout_programs_coach_user_id_fkey FOREIGN KEY (coach_user_id) REFERENCES users(id) ON DELETE SET NULL';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'workout_days_workout_program_id_fkey') THEN
    EXECUTE 'ALTER TABLE workout_days ADD CONSTRAINT workout_days_workout_program_id_fkey FOREIGN KEY (workout_program_id) REFERENCES workout_programs(id) ON DELETE CASCADE';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_workout_exercises_exercise_library') THEN
    EXECUTE 'ALTER TABLE workout_exercises ADD CONSTRAINT fk_workout_exercises_exercise_library FOREIGN KEY (exercise_library_id) REFERENCES exercise_library(id) ON DELETE SET NULL';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'workout_exercises_workout_day_id_fkey') THEN
    EXECUTE 'ALTER TABLE workout_exercises ADD CONSTRAINT workout_exercises_workout_day_id_fkey FOREIGN KEY (workout_day_id) REFERENCES workout_days(id) ON DELETE CASCADE';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'nutrition_programs_client_user_id_fkey') THEN
    EXECUTE 'ALTER TABLE nutrition_programs ADD CONSTRAINT nutrition_programs_client_user_id_fkey FOREIGN KEY (client_user_id) REFERENCES users(id) ON DELETE CASCADE';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'nutrition_programs_coach_user_id_fkey') THEN
    EXECUTE 'ALTER TABLE nutrition_programs ADD CONSTRAINT nutrition_programs_coach_user_id_fkey FOREIGN KEY (coach_user_id) REFERENCES users(id) ON DELETE SET NULL';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'nutrition_meals_nutrition_program_id_fkey') THEN
    EXECUTE 'ALTER TABLE nutrition_meals ADD CONSTRAINT nutrition_meals_nutrition_program_id_fkey FOREIGN KEY (nutrition_program_id) REFERENCES nutrition_programs(id) ON DELETE CASCADE';
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS users_email_key ON public.users USING btree (email);

CREATE UNIQUE INDEX IF NOT EXISTS client_onboarding_user_id_key ON public.client_onboarding USING btree (user_id);

CREATE INDEX IF NOT EXISTS idx_coach_packages_coach_user_id ON public.coach_packages USING btree (coach_user_id);

CREATE INDEX IF NOT EXISTS idx_exercise_library_name ON public.exercise_library USING gin (to_tsvector('english'::regconfig, (canonical_name)::text));

CREATE INDEX IF NOT EXISTS idx_exercise_library_canonical_name ON public.exercise_library USING btree (canonical_name);

CREATE INDEX IF NOT EXISTS idx_subscriptions_coach_created ON public.subscriptions USING btree (coach_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_subscriptions_client_active ON public.subscriptions USING btree (client_user_id, status);

CREATE INDEX IF NOT EXISTS idx_subs_coach_created ON public.subscriptions USING btree (coach_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_subs_client_status ON public.subscriptions USING btree (client_user_id, status);

CREATE UNIQUE INDEX IF NOT EXISTS uq_subscriptions_ref ON public.subscriptions USING btree (subscription_ref);

CREATE UNIQUE INDEX IF NOT EXISTS uq_subscriptions_client_package_active ON public.subscriptions USING btree (client_user_id, package_id) WHERE (status = ANY (ARRAY['pending'::text, 'active'::text]));

CREATE UNIQUE INDEX IF NOT EXISTS one_active_workout_per_client ON public.workout_programs USING btree (client_user_id) WHERE (is_active = true);

CREATE UNIQUE INDEX IF NOT EXISTS uq_workout_active_per_client ON public.workout_programs USING btree (client_user_id) WHERE (is_active = true);

CREATE INDEX IF NOT EXISTS idx_workout_exercises_exercise_library_id ON public.workout_exercises USING btree (exercise_library_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_nutrition_active_per_client ON public.nutrition_programs USING btree (client_user_id) WHERE (is_active = true);

CREATE UNIQUE INDEX IF NOT EXISTS uq_meal_type_per_program ON public.nutrition_meals USING btree (nutrition_program_id, meal_type);
