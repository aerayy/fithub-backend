-- 063: prod ile şema eşitliği (15 Eyl 2026).
-- Temiz kurulum (000_baseline + 001..062) prod'la kolon bazında karşılaştırıldı; prod'da ELLE
-- eklenmiş olup migration'ı olmayan 2 tablo + 5 kolon burada idempotent olarak tanımlanır.
-- Prod'da no-op (hepsi zaten var); staging/CI'da eksikleri tamamlar.

CREATE TABLE IF NOT EXISTS coach_reviews (
    id SERIAL NOT NULL,
    client_user_id integer NOT NULL,
    coach_user_id integer NOT NULL,
    rating integer NOT NULL,
    comment text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT coach_reviews_rating_check CHECK (((rating >= 1) AND (rating <= 5))),
    CONSTRAINT coach_reviews_pkey PRIMARY KEY (id),
    CONSTRAINT coach_reviews_client_user_id_coach_user_id_key UNIQUE (client_user_id, coach_user_id)
);

CREATE TABLE IF NOT EXISTS coach_transformations (
    id SERIAL NOT NULL,
    coach_user_id integer NOT NULL,
    before_image_url text NOT NULL,
    after_image_url text NOT NULL,
    student_name text DEFAULT 'Anonim'::text,
    weight_lost_kg numeric(5,1),
    duration_weeks integer,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT coach_transformations_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_coach_reviews_coach ON coach_reviews USING btree (coach_user_id);

CREATE INDEX IF NOT EXISTS idx_transformations_coach ON coach_transformations USING btree (coach_user_id, is_active);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'coach_reviews_client_user_id_fkey') THEN
    ALTER TABLE coach_reviews ADD CONSTRAINT coach_reviews_client_user_id_fkey FOREIGN KEY (client_user_id) REFERENCES users(id) ON DELETE CASCADE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'coach_reviews_coach_user_id_fkey') THEN
    ALTER TABLE coach_reviews ADD CONSTRAINT coach_reviews_coach_user_id_fkey FOREIGN KEY (coach_user_id) REFERENCES users(id) ON DELETE CASCADE;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'coach_transformations_coach_user_id_fkey') THEN
    ALTER TABLE coach_transformations ADD CONSTRAINT coach_transformations_coach_user_id_fkey FOREIGN KEY (coach_user_id) REFERENCES users(id) ON DELETE CASCADE;
  END IF;
END $$;

ALTER TABLE food_items ADD COLUMN IF NOT EXISTS brand_owner TEXT;
ALTER TABLE food_items ADD COLUMN IF NOT EXISTS ingredients TEXT;
ALTER TABLE food_localization_tr ADD COLUMN IF NOT EXISTS category_tr TEXT;
ALTER TABLE food_localization_tr ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE meal_photos ADD COLUMN IF NOT EXISTS notes TEXT;
