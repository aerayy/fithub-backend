-- Migration: Import BeGreens nutrition database (497 Turkish foods)
-- Source: begreens_app.sql nutritionunits table

-- Add piece_weight_g and serving_unit to food_items if not exists
ALTER TABLE food_items ADD COLUMN IF NOT EXISTS piece_weight_g DECIMAL(10,2);
ALTER TABLE food_items ADD COLUMN IF NOT EXISTS serving_unit VARCHAR(50) DEFAULT 'g';
ALTER TABLE food_items ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;
ALTER TABLE food_items ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'usda';

-- Insert BeGreens foods
DO $$
DECLARE
  fid INTEGER;
BEGIN

  -- Ceviz
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Ceviz', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 31.0, 1.2, 2.97, 0.48, 0.34, 26.15)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Ceviz')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Hindi Göğüs
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Hindi Göğüs', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 116.0, 21.27, 3.46, 0.0, 0.0, 37.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Hindi Göğüs')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yulaf Ezmesi (Müsli Olan)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yulaf Ezmesi (Müsli Olan)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 368.0, 11.0, 9.0, 57.0, 9.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yulaf Ezmesi (Müsli Olan)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kırmızı Et
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kırmızı Et', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 133.0, 23.0, 5.0, 0.0, 0.0, 60.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kırmızı Et')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çipura
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çipura', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 96.0, 19.6, 1.9, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çipura')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Levrek
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Levrek', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 97.0, 18.43, 2.0, 0.0, 0.0, 68.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Levrek')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Somon
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Somon', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 231.0, 26.0, 13.0, 0.0, 0.0, 60.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Somon')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Hindi Füme
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Hindi Füme', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 170.0, 29.0, 5.0, 0.0, 0.0, 996.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Hindi Füme')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Jasmine Pirinç
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Jasmine Pirinç', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 340.0, 6.0, 0.0, 78.0, 0.0, 20.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Jasmine Pirinç')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Basmati Pirinç
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Basmati Pirinç', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 365.0, 7.0, 1.0, 80.0, 1.0, 5.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Basmati Pirinç')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Baldo Pirinç
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Baldo Pirinç', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 350.0, 6.0, 1.0, 77.0, 1.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Baldo Pirinç')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Patates
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Patates', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 77.0, 2.0, 0.0, 17.0, 2.0, 6.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Patates')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tatlı Patates
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tatlı Patates', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 86.0, 2.0, 0.0, 20.0, 3.0, 55.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tatlı Patates')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Makarna
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Makarna', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 400.0, 12.0, 2.0, 68.0, 2.0, 131.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Makarna')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kinoa (çiğ)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kinoa (çiğ)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 367.0, 14.0, 6.0, 64.0, 7.0, 5.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kinoa (çiğ)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Siyah Pirinç
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Siyah Pirinç', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 267.0, 8.0, 3.0, 57.0, 3.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Siyah Pirinç')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kara Buğday
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kara Buğday', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 343.0, 13.0, 3.0, 72.0, 10.0, 1.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kara Buğday')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Rice Cake (Pirinç Patlağı)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Rice Cake (Pirinç Patlağı)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 30.0, 0.5, 0.0, 7.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Rice Cake (Pirinç Patlağı)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Rice Cream
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Rice Cream', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 338.0, 7.0, 2.0, 73.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Rice Cream')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Rice King
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Rice King', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 348.0, 0.0, 0.0, 78.0, 2.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Rice King')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Hurma
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Hurma', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 28.0, 0.18, 0.02, 7.5, 0.67, 0.1)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Hurma')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kepekli Pirinç
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kepekli Pirinç', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 350.0, 7.0, 2.0, 74.0, 2.0, 10.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kepekli Pirinç')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yaban Mersini
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yaban Mersini', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 44.0, 0.0, 0.0, 8.0, 3.0, 6.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yaban Mersini')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Zeytin Yağı (13,5 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Zeytin Yağı (13,5 gr)', NULL, 'Yemek Kaşığı', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 119.0, 0.0, 13.5, 0.03, 0.0, 0.27)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Zeytin Yağı (13,5 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Whey Protein Tozu 1.5 servis
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Whey Protein Tozu 1.5 servis', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 178.86, 33.75, 3.42, 1.5, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Whey Protein Tozu 1.5 servis')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Ananas
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Ananas', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 50.0, 1.0, 0.0, 13.0, 1.0, 1.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Ananas')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yeşillik Salatası 1 Porsiyon (100-150 Gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yeşillik Salatası 1 Porsiyon (100-150 Gr)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 30.0, 0.5, 0.0, 3.49, 2.2, 7.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yeşillik Salatası 1 Porsiyon (100-150 Gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çiğ Badem
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çiğ Badem', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 12.0, 0.44, 1.06, 0.39, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çiğ Badem')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kaju
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kaju', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 5.53, 0.18, 0.44, 0.3, 0.0, 0.12)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kaju')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Fındık
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Fındık', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 13.0, 0.3, 1.22, 0.33, 0.19, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Fındık')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kabak Çekirdeği
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kabak Çekirdeği', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 560.0, 24.0, 46.0, 14.0, 9.0, 18.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kabak Çekirdeği')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yer Fıstığı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yer Fıstığı', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 567.0, 26.0, 49.0, 16.0, 9.0, 18.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yer Fıstığı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yoğurt (Laktozsuz)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yoğurt (Laktozsuz)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 64.0, 5.0, 2.0, 8.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yoğurt (Laktozsuz)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Süt (Laktozsuz)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Süt (Laktozsuz)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 46.0, 3.0, 2.0, 5.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Süt (Laktozsuz)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kuru Üzüm
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kuru Üzüm', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 304.0, 3.0, 1.0, 67.0, 3.0, 9.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kuru Üzüm')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Salatalık
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Salatalık', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 18.0, 0.78, 0.13, 4.36, 0.6, 2.4)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Salatalık')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kefir (Laktozsuz)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kefir (Laktozsuz)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 60.0, 3.0, 3.0, 5.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kefir (Laktozsuz)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kepekli Ekmek
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kepekli Ekmek', NULL, 'Dilim', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 54.0, 1.51, 0.38, 11.14, 1.62, 150.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kepekli Ekmek')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tam Tahıllı Ekmek
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tam Tahıllı Ekmek', NULL, 'Dilim', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 68.0, 1.91, 0.87, 12.88, 1.44, 121.2)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tam Tahıllı Ekmek')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tam Yumurta
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tam Yumurta', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 72.0, 6.28, 4.76, 0.36, 0.0, 71.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tam Yumurta')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yumurta Beyazı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yumurta Beyazı', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 16.0, 4.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yumurta Beyazı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tuz (Himalaya Tuzu)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tuz (Himalaya Tuzu)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tuz (Himalaya Tuzu)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kapya Biber
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kapya Biber', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 19.0, 0.65, 0.25, 3.2, 1.8, 2.5)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kapya Biber')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yeşil Biber
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yeşil Biber', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 14.0, 0.5, 0.11, 3.16, 0.45, 1.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yeşil Biber')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sade Soda
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sade Soda', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 850.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sade Soda')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Limon
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Limon', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 43.0, 0.44, 0.36, 8.73, 1.41, 3.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Limon')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Zma
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Zma', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Zma')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Glutamine
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Glutamine', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Glutamine')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Cla 1 Adet (Öğünden Önce ya da Hemen Sonra)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Cla 1 Adet (Öğünden Önce ya da Hemen Sonra)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 9.0, 0.0, 1.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Cla 1 Adet (Öğünden Önce ya da Hemen Sonra)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- L-Carnitine Thermo
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('L-Carnitine Thermo', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'L-Carnitine Thermo')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gainer Pro
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gainer Pro', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 190.0, 0.0, 0.0, 47.5, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gainer Pro')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Chromium Picolinate (Proteinocean Flava)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Chromium Picolinate (Proteinocean Flava)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Chromium Picolinate (Proteinocean Flava)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Şekersiz Filtre Kahve
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Şekersiz Filtre Kahve', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Şekersiz Filtre Kahve')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sade Türk Kahvesi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sade Türk Kahvesi', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 7.0, 0.42, 0.52, 0.06, 2.65, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sade Türk Kahvesi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Nescafe Gold
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Nescafe Gold', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Nescafe Gold')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Bcaa 1 Porsiyon
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Bcaa 1 Porsiyon', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Bcaa 1 Porsiyon')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çinko 1 Servis 50 Mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çinko 1 Servis 50 Mg', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çinko 1 Servis 50 Mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yeşil Elma
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yeşil Elma', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 52.0, 0.4, 0.17, 12.25, 2.52, 0.9)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yeşil Elma')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Muz
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Muz', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 151.0, 1.85, 0.56, 38.83, 4.42, 1.7)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Muz')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sirke
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sirke', NULL, 'Yemek Kaşığı', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sirke')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Nac 600
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Nac 600', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Nac 600')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Omega 3 1000 Mg (leda)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Omega 3 1000 Mg (leda)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Omega 3 1000 Mg (leda)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tuz (Himalaya Tuzu)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tuz (Himalaya Tuzu)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tuz (Himalaya Tuzu)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çiğ Kabak Çekirdeği
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çiğ Kabak Çekirdeği', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 610.0, 30.0, 50.0, 10.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çiğ Kabak Çekirdeği')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Arginine
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Arginine', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Arginine')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Creatine 5 Gr
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Creatine 5 Gr', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Creatine 5 Gr')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Creatine
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Creatine', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Creatine')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Probiotic
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Probiotic', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Probiotic')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yağsız Dana Kıyma Sote (Sebzeli Pişirilsin)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yağsız Dana Kıyma Sote (Sebzeli Pişirilsin)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 133.0, 23.0, 5.0, 0.0, 0.0, 60.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yağsız Dana Kıyma Sote (Sebzeli Pişirilsin)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Az Yağlı Dana Kıyma (Sebzelerle Sote Yapalım)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Az Yağlı Dana Kıyma (Sebzelerle Sote Yapalım)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 248.0, 18.65, 13.63, 0.46, 0.0, 60.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Az Yağlı Dana Kıyma (Sebzelerle Sote Yapalım)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Multivitamin (herbina)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Multivitamin (herbina)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Multivitamin (herbina)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- 1000 Mg Ester C Vitamini
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('1000 Mg Ester C Vitamini', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, '1000 Mg Ester C Vitamini')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Maydanoz
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Maydanoz', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 37.0, 3.0, 1.0, 3.0, 3.0, 75.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Maydanoz')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Calcium 600 800 Mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Calcium 600 800 Mg', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Calcium 600 800 Mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- D Vitamini 1000 İu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('D Vitamini 1000 İu', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'D Vitamini 1000 İu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Arimidex (3 GÜNDE 1)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Arimidex (3 GÜNDE 1)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Arimidex (3 GÜNDE 1)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Cabaser 0.5 Mg (21 Günde 1  Tablet)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Cabaser 0.5 Mg (21 Günde 1  Tablet)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Cabaser 0.5 Mg (21 Günde 1  Tablet)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Proviron 25 Mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Proviron 25 Mg', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Proviron 25 Mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Liv 52  Karaciğer koruyucu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Liv 52  Karaciğer koruyucu', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Liv 52  Karaciğer koruyucu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Cystone Böbrek Koruyucu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Cystone Böbrek Koruyucu', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Cystone Böbrek Koruyucu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- E Vitamini 400 İu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('E Vitamini 400 İu', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'E Vitamini 400 İu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gilabura ve Enginar Suyu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gilabura ve Enginar Suyu', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gilabura ve Enginar Suyu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Letrasan
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Letrasan', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Letrasan')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Probiotıc
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Probiotıc', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Probiotıc')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Koenzim Q10 100 mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Koenzim Q10 100 mg', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Koenzim Q10 100 mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Avokado
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Avokado', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 160.0, 2.0, 15.0, 9.0, 7.0, 7.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Avokado')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Limon
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Limon', NULL, 'yarım adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 21.5, 0.22, 0.18, 4.37, 0.7, 1.5)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Limon')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Carsil
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Carsil', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Carsil')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Dana Ciğer
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Dana Ciğer', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 200.0, 28.0, 6.0, 4.0, 0.0, 78.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Dana Ciğer')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yasemin Pirinç
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yasemin Pirinç', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 340.0, 6.0, 0.0, 78.0, 0.0, 20.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yasemin Pirinç')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gün Aşırı 1 Arimidex
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gün Aşırı 1 Arimidex', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gün Aşırı 1 Arimidex')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yulaf Ezmesi (İNCE YAPRAKLI ETİ LİFALİF)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yulaf Ezmesi (İNCE YAPRAKLI ETİ LİFALİF)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 389.0, 17.0, 7.0, 66.0, 11.0, 2.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yulaf Ezmesi (İNCE YAPRAKLI ETİ LİFALİF)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Prenox CAGE
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Prenox CAGE', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Prenox CAGE')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Siyah Zeytin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Siyah Zeytin', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 5.0, 0.03, 0.44, 0.24, 0.06, 29.4)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Siyah Zeytin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Glucosamine Msm
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Glucosamine Msm', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Glucosamine Msm')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Testosteron Boost
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Testosteron Boost', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Testosteron Boost')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Haşlanmış Brokoli
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Haşlanmış Brokoli', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 9.0, 3.0, 0.0, 2.0, 2.0, 15.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Haşlanmış Brokoli')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yeşil Çay
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yeşil Çay', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yeşil Çay')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yağsız Dana Kıyma Köfte
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yağsız Dana Kıyma Köfte', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 200.0, 19.0, 8.0, 0.0, 0.0, 60.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yağsız Dana Kıyma Köfte')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yeşil Elma
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yeşil Elma', NULL, 'yarım adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 26.0, 0.2, 0.09, 6.12, 1.26, 0.45)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yeşil Elma')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tribulus
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tribulus', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tribulus')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Beta Alanine
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Beta Alanine', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Beta Alanine')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Danone Activia Sade Probiyotik Yoğurt
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Danone Activia Sade Probiyotik Yoğurt', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 64.0, 3.7, 3.5, 4.4, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Danone Activia Sade Probiyotik Yoğurt')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Lor Peyniri
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Lor Peyniri', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 72.0, 10.0, 0.0, 7.0, 0.0, 372.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Lor Peyniri')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Chia Tohumu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Chia Tohumu', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 500.0, 17.0, 31.0, 42.0, 34.0, 16.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Chia Tohumu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Speman
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Speman', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Speman')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Nolvadex 20 Mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Nolvadex 20 Mg', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Nolvadex 20 Mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Burner
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Burner', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Burner')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kahve (Filtre-Sade-Türk Kahvesi)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kahve (Filtre-Sade-Türk Kahvesi)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kahve (Filtre-Sade-Türk Kahvesi)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- CHORİOMON  7 X 1500 İU 3 Günde 1
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('CHORİOMON  7 X 1500 İU 3 Günde 1', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'CHORİOMON  7 X 1500 İU 3 Günde 1')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- 1 Bardak Su
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('1 Bardak Su', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, '1 Bardak Su')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Desiferol D. Vit 2000 İu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Desiferol D. Vit 2000 İu', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Desiferol D. Vit 2000 İu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Blueberry
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Blueberry', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 44.0, 0.0, 0.0, 8.0, 3.0, 6.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Blueberry')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Amino Asit (Tablet-Bcaa-Glutamine Vb)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Amino Asit (Tablet-Bcaa-Glutamine Vb)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Amino Asit (Tablet-Bcaa-Glutamine Vb)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Keten Tohumu (1 Tatlı Kaşığı)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Keten Tohumu (1 Tatlı Kaşığı)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 27.0, 0.91, 2.11, 1.44, 1.37, 1.5)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Keten Tohumu (1 Tatlı Kaşığı)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Hindistan Cevizi Yağı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Hindistan Cevizi Yağı', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 900.0, 0.0, 100.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Hindistan Cevizi Yağı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- B12
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('B12', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'B12')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Alpha Lipoic Acid 400 Mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Alpha Lipoic Acid 400 Mg', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Alpha Lipoic Acid 400 Mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Demir (FERRUM FORT 100 MG)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Demir (FERRUM FORT 100 MG)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Demir (FERRUM FORT 100 MG)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Zeytin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Zeytin', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 8.0, 0.07, 0.84, 0.04, 0.0, 131.52)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Zeytin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sade Activia
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sade Activia', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 64.0, 3.7, 3.5, 4.4, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sade Activia')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Magnezyum
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Magnezyum', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Magnezyum')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Zerdeçal Tozu (Tatlı Kaşığı)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Zerdeçal Tozu (Tatlı Kaşığı)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 16.0, 0.48, 0.16, 3.36, 1.14, 1.35)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Zerdeçal Tozu (Tatlı Kaşığı)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çemen Otu (20 Gr Porsiyon)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çemen Otu (20 Gr Porsiyon)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 64.6, 4.6, 1.2, 11.6, 0.0, 13.4)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çemen Otu (20 Gr Porsiyon)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tarçın
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tarçın', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 247.0, 4.0, 1.0, 81.0, 53.0, 10.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tarçın')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sarımsak (Porsiyon 10 Gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sarımsak (Porsiyon 10 Gr)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 15.0, 0.64, 0.05, 3.31, 0.21, 1.7)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sarımsak (Porsiyon 10 Gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çörekotu Yağı (1 Tatlı Kaşığı)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çörekotu Yağı (1 Tatlı Kaşığı)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 28.0, 0.85, 2.4, 1.3, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çörekotu Yağı (1 Tatlı Kaşığı)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Detoksfit
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Detoksfit', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 45.0, 2.23, 1.15, 7.53, 2.22, 0.15)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Detoksfit')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Green Detox
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Green Detox', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 28.0, 2.42, 0.48, 2.52, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Green Detox')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Milk Thistle
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Milk Thistle', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Milk Thistle')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Enginar Ekstresi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Enginar Ekstresi', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Enginar Ekstresi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çilek
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çilek', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 4.0, 0.08, 0.04, 0.92, 0.24, 0.12)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çilek')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kabuklu Tuzsuz Fıstık
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kabuklu Tuzsuz Fıstık', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 6.0, 0.26, 0.49, 0.16, 0.09, 0.18)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kabuklu Tuzsuz Fıstık')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kırmızı Meyve 50 Gr (Yabanmersini, Çilek, Frambuaz, Böğürtlen)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kırmızı Meyve 50 Gr (Yabanmersini, Çilek, Frambuaz, Böğürtlen)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 40.0, 0.4, 0.2, 4.6, 1.2, 0.6)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kırmızı Meyve 50 Gr (Yabanmersini, Çilek, Frambuaz, Böğürtlen)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kepekli Etimek
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kepekli Etimek', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 36.0, 0.95, 0.26, 7.23, 0.37, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kepekli Etimek')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Bitter Çikolata Yüzde 80
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Bitter Çikolata Yüzde 80', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 546.0, 5.0, 31.0, 61.0, 7.0, 24.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Bitter Çikolata Yüzde 80')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Mantar (100 Gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Mantar (100 Gram)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 22.0, 3.09, 0.34, 3.26, 1.0, 5.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Mantar (100 Gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Wasa (Original)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Wasa (Original)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 43.0, 1.17, 0.26, 7.8, 2.6, 0.13)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Wasa (Original)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Citrulline Malate
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Citrulline Malate', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Citrulline Malate')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Thermonator Rıpped
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Thermonator Rıpped', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Thermonator Rıpped')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Badem Sütü 250ml
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Badem Sütü 250ml', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 40.0, 1.48, 2.75, 1.45, 0.5, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Badem Sütü 250ml')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Humus
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Humus', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 242.0, 6.0, 18.0, 13.0, 6.0, 141.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Humus')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Mercimek (100gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Mercimek (100gr)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 116.0, 9.0, 0.4, 20.0, 0.0, 0.2)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Mercimek (100gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Soya Kıyma
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Soya Kıyma', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 298.0, 45.0, 1.0, 20.0, 14.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Soya Kıyma')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Carbo Pro Biogain (4 Ölçek)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Carbo Pro Biogain (4 Ölçek)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 380.0, 0.0, 0.0, 95.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Carbo Pro Biogain (4 Ölçek)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BCAA Biogain 2:1:1 (Yarım Ölçek)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BCAA Biogain 2:1:1 (Yarım Ölçek)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BCAA Biogain 2:1:1 (Yarım Ölçek)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Vitargo 75 Gr
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Vitargo 75 Gr', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 280.0, 0.0, 0.0, 69.0, 0.0, 270.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Vitargo 75 Gr')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Vitargo
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Vitargo', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 373.0, 0.0, 0.0, 92.0, 0.0, 180.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Vitargo')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Whey Protein
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Whey Protein', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 119.24, 22.5, 2.28, 1.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Whey Protein')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gün Kurusu Kayısı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gün Kurusu Kayısı', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 24.0, 0.34, 0.05, 6.26, 0.73, 1.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gün Kurusu Kayısı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Ton Balığı Süzülmüş
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Ton Balığı Süzülmüş', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 95.0, 21.0, 0.0, 1.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Ton Balığı Süzülmüş')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çörçil (1 Adet Soda-1 Gr Tuz-Yarım Adet Limon)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çörçil (1 Adet Soda-1 Gr Tuz-Yarım Adet Limon)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çörçil (1 Adet Soda-1 Gr Tuz-Yarım Adet Limon)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Ton Balığı (Yağı Süzülmüş)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Ton Balığı (Yağı Süzülmüş)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 95.0, 21.4, 0.23, 0.8, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Ton Balığı (Yağı Süzülmüş)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Bcaa Glutamine Xpress
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Bcaa Glutamine Xpress', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Bcaa Glutamine Xpress')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gainer Pro 50 Gr
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gainer Pro 50 Gr', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 195.3, 9.0, 1.39, 35.45, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gainer Pro 50 Gr')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gainer Pro 100 Gr
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gainer Pro 100 Gr', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 390.6, 18.0, 2.78, 70.9, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gainer Pro 100 Gr')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BCAA 2:1:1   GLUTAMINE
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BCAA 2:1:1   GLUTAMINE', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BCAA 2:1:1   GLUTAMINE')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- 1 Porsiyon Hydroxycut
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('1 Porsiyon Hydroxycut', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, '1 Porsiyon Hydroxycut')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sebzeli Bulgur Pilavı (1 yk-20 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sebzeli Bulgur Pilavı (1 yk-20 gr)', NULL, 'Yemek Kaşığı', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 14.0, 0.38, 0.37, 2.32, 0.55, 0.7)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sebzeli Bulgur Pilavı (1 yk-20 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Grenade
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Grenade', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Grenade')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Zencefil   Limon Su (Kaynatılarak İçilecek)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Zencefil   Limon Su (Kaynatılarak İçilecek)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 4.85, 1.1, 0.5, 1.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Zencefil   Limon Su (Kaynatılarak İçilecek)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- 1 Bardak Su- Yarım Limon- 1 Gr Tuz
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('1 Bardak Su- Yarım Limon- 1 Gr Tuz', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, '1 Bardak Su- Yarım Limon- 1 Gr Tuz')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- IMMUNOLEX (4 Tablet)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('IMMUNOLEX (4 Tablet)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'IMMUNOLEX (4 Tablet)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kayısı Çayı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kayısı Çayı', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kayısı Çayı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Superfresh Ton Balığı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Superfresh Ton Balığı', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 170.0, 20.2, 9.9, 0.0, 0.0, 1.3)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Superfresh Ton Balığı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Rosto
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Rosto', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 162.6, 11.2, 11.0, 4.7, 0.7, 0.6)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Rosto')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kavurma
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kavurma', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 274.5, 22.5, 20.5, 0.0, 0.0, 1.7)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kavurma')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Arginine
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Arginine', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Arginine')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kuru Kayısı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kuru Kayısı', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 14.0, 0.42, 0.12, 3.34, 0.6, 0.3)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kuru Kayısı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Solgar 5-HTP
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Solgar 5-HTP', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Solgar 5-HTP')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Zaditen 1 Mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Zaditen 1 Mg', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Zaditen 1 Mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Nexium 20 Mg (SABAH AÇ KARNINA ALINACAK)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Nexium 20 Mg (SABAH AÇ KARNINA ALINACAK)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Nexium 20 Mg (SABAH AÇ KARNINA ALINACAK)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Fit grains pirinç patlağı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Fit grains pirinç patlağı', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 400.0, 0.0, 0.0, 70.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Fit grains pirinç patlağı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tavuk Döner
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tavuk Döner', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 163.0, 23.0, 30.0, 0.0, 0.0, 650.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tavuk Döner')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- LEVOTIRON 25 MCG
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('LEVOTIRON 25 MCG', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'LEVOTIRON 25 MCG')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- TIROMEL 25 MCG
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('TIROMEL 25 MCG', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'TIROMEL 25 MCG')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Livercare
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Livercare', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Livercare')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sıcak Su
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sıcak Su', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sıcak Su')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kafein kapsül
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kafein kapsül', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kafein kapsül')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- AlphMen
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('AlphMen', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'AlphMen')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Papatya Çayı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Papatya Çayı', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Papatya Çayı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tatlı Patates
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tatlı Patates', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 86.0, 2.0, 0.0, 20.0, 3.0, 55.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tatlı Patates')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Muz
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Muz', NULL, 'yarım adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 75.0, 0.9, 0.2, 19.4, 2.2, 0.8)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Muz')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Domates
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Domates', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 20.0, 0.9, 0.0, 4.2, 1.32, 0.01)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Domates')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Arimidex 1 adet Her Gün
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Arimidex 1 adet Her Gün', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Arimidex 1 adet Her Gün')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Galeta (1 küçük boy- 8 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Galeta (1 küçük boy- 8 gram)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 31.0, 0.8, 0.3, 6.0, 0.26, 40.8)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Galeta (1 küçük boy- 8 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tam Yumurta
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tam Yumurta', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 72.0, 6.2, 4.7, 0.3, 0.0, 71.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tam Yumurta')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Besmele Çekip Antrenmana Başlıyoruz :)  Oruçluyuz Unutmayalım..
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Besmele Çekip Antrenmana Başlıyoruz :)  Oruçluyuz Unutmayalım..', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Besmele Çekip Antrenmana Başlıyoruz :)  Oruçluyuz Unutmayalım..')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Haşlanmış Nohut
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Haşlanmış Nohut', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 200.0, 9.0, 0.0, 27.0, 8.0, 7.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Haşlanmış Nohut')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Arimidex (2 GÜNDE 1)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Arimidex (2 GÜNDE 1)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Arimidex (2 GÜNDE 1)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Haşlanmış tavuk göğüs
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Haşlanmış tavuk göğüs', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 120.0, 20.0, 1.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Haşlanmış tavuk göğüs')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yeşil Mercimek (Haşlanmış)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yeşil Mercimek (Haşlanmış)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 300.0, 23.0, 1.0, 37.0, 26.0, 13.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yeşil Mercimek (Haşlanmış)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Leblebi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Leblebi', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 300.0, 20.0, 3.0, 38.0, 21.0, 25.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Leblebi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- SANMARKO L-KARNİTİN SWİG 3000 MG SHOT
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('SANMARKO L-KARNİTİN SWİG 3000 MG SHOT', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 13.0, 3.3, 0.1, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'SANMARKO L-KARNİTİN SWİG 3000 MG SHOT')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Meksika Fasulyesi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Meksika Fasulyesi', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 329.0, 20.0, 1.0, 63.0, 13.0, 5.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Meksika Fasulyesi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Börülce
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Börülce', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 118.0, 9.0, 2.0, 16.0, 7.0, 145.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Börülce')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sirke(1 tatlı kaşığı)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sirke(1 tatlı kaşığı)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sirke(1 tatlı kaşığı)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Limon ( 1/4)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Limon ( 1/4)', NULL, 'Dilim', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 11.0, 0.11, 0.05, 2.1, 0.7, 0.75)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Limon ( 1/4)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Beyaz Peynir (1 orta dilim-30 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Beyaz Peynir (1 orta dilim-30 gr)', NULL, 'Dilim', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 93.0, 6.11, 7.29, 0.76, 0.0, 211.2)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Beyaz Peynir (1 orta dilim-30 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Bal (1 tatlı kaşığı)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Bal (1 tatlı kaşığı)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 30.0, 0.04, 0.0, 8.24, 0.0, 0.4)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Bal (1 tatlı kaşığı)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sebze Yemeği
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sebze Yemeği', NULL, 'Yemek Kaşığı', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 14.0, 0.58, 0.46, 1.69, 0.77, 24.25)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sebze Yemeği')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çorba ( 1 küçük kase)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çorba ( 1 küçük kase)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 57.0, 1.0, 2.5, 7.5, 0.65, 335.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çorba ( 1 küçük kase)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Ayran (200 ml)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Ayran (200 ml)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 100.0, 4.0, 5.0, 9.6, 0.0, 624.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Ayran (200 ml)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yoğurt
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yoğurt', NULL, 'Yemek Kaşığı', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 27.0, 1.56, 1.46, 2.1, 0.0, 20.7)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yoğurt')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kiraz
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kiraz', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 4.0, 0.0, 0.0, 1.12, 0.15, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kiraz')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yeşil Erik
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yeşil Erik', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 9.0, 0.14, 0.0, 2.28, 0.28, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yeşil Erik')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Karpuz (1 üçgen dilim-50 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Karpuz (1 üçgen dilim-50 gr)', NULL, 'Dilim', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 15.0, 0.3, 0.0, 3.78, 0.2, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Karpuz (1 üçgen dilim-50 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kavun ( 1 ince dilim - 180 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kavun ( 1 ince dilim - 180 gram)', NULL, 'Dilim', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 50.0, 2.0, 0.0, 11.84, 1.62, 16.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kavun ( 1 ince dilim - 180 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Balkabağı (1 kalın dilim -240 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Balkabağı (1 kalın dilim -240 gr)', NULL, 'Dilim', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 60.0, 2.64, 0.31, 11.02, 5.18, 2.4)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Balkabağı (1 kalın dilim -240 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Züber Bar
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Züber Bar', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 125.0, 2.6, 4.32, 19.32, 5.4, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Züber Bar')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Muscle Station Protein Bar
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Muscle Station Protein Bar', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 158.0, 7.11, 8.45, 20.9, 7.9, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Muscle Station Protein Bar')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Izgara Sebze ( 120 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Izgara Sebze ( 120 gr)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 88.0, 4.21, 0.8, 15.23, 5.74, 202.98)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Izgara Sebze ( 120 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Pancar
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Pancar', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 100.0, 1.0, 0.0, 10.0, 2.0, 24.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Pancar')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Karabuğday Patlağı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Karabuğday Patlağı', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 34.0, 0.2, 0.34, 7.1, 0.8, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Karabuğday Patlağı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kabak Sote
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kabak Sote', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 35.0, 2.0, 2.0, 3.0, 1.0, 98.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kabak Sote')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Fırın Sebze - 280 gr
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Fırın Sebze - 280 gr', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 153.0, 4.39, 7.02, 17.34, 6.93, 754.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Fırın Sebze - 280 gr')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kuru Erik (Mürdüm)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kuru Erik (Mürdüm)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 26.0, 0.3, 0.1, 5.65, 0.94, 1.1)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kuru Erik (Mürdüm)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- SANMARKO L-KARNİTİN 1000 ML (SERVİS 30 ML)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('SANMARKO L-KARNİTİN 1000 ML (SERVİS 30 ML)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 6.0, 1.5, 0.1, 0.1, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'SANMARKO L-KARNİTİN 1000 ML (SERVİS 30 ML)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Fragment 176-191
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Fragment 176-191', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Fragment 176-191')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- CHEERIOS
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('CHEERIOS', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 400.0, 9.0, 10.0, 75.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'CHEERIOS')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Pirinç Patlağı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Pirinç Patlağı', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 300.0, 5.0, 1.0, 78.0, 2.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Pirinç Patlağı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Vegan Köfte
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Vegan Köfte', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 241.0, 20.0, 14.0, 8.0, 10.0, 10.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Vegan Köfte')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Melatonin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Melatonin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Melatonin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- D Vitamini 2000 iu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('D Vitamini 2000 iu', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'D Vitamini 2000 iu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yeşil Erik
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yeşil Erik', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 9.0, 0.14, 0.06, 2.28, 0.28, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yeşil Erik')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- LEDAX C VİTAMİNİ 1000 MG ŞASE
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('LEDAX C VİTAMİNİ 1000 MG ŞASE', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'LEDAX C VİTAMİNİ 1000 MG ŞASE')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- LEDA D VİTAMİN 1000 iu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('LEDA D VİTAMİN 1000 iu', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'LEDA D VİTAMİN 1000 iu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- HEPA 4
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('HEPA 4', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'HEPA 4')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Meyve
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Meyve', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 50.0, 0.0, 0.0, 12.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Meyve')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kızıl Pirinç
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kızıl Pirinç', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 271.0, 69.0, 10.0, 860.0, 3.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kızıl Pirinç')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- EFEDRİN
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('EFEDRİN', NULL, 'yarım adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'EFEDRİN')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- EFEDRİN
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('EFEDRİN', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'EFEDRİN')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Fındık Ezmesi (Fit Nut)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Fındık Ezmesi (Fit Nut)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 688.0, 14.0, 65.0, 6.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Fındık Ezmesi (Fit Nut)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Carbo Pro Biogain (2 Ölçek 50 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Carbo Pro Biogain (2 Ölçek 50 gr)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 190.0, 0.0, 0.0, 47.5, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Carbo Pro Biogain (2 Ölçek 50 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Carbo Pro Biogain (3 Ölçek 75 gr )
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Carbo Pro Biogain (3 Ölçek 75 gr )', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 285.0, 0.0, 0.0, 71.5, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Carbo Pro Biogain (3 Ölçek 75 gr )')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kepekli Makarna
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kepekli Makarna', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 400.0, 12.0, 2.0, 68.0, 10.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kepekli Makarna')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Eti Form Diyet Bisküvi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Eti Form Diyet Bisküvi', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 226.0, 2.69, 8.18, 36.51, 3.81, 0.22)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Eti Form Diyet Bisküvi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- LEDAX ÇİNKO
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('LEDAX ÇİNKO', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'LEDAX ÇİNKO')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Havuç (orta boy- 40 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Havuç (orta boy- 40 gram)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 16.0, 0.37, 0.1, 3.83, 1.03, 27.6)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Havuç (orta boy- 40 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kabak (orta boy-150 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kabak (orta boy-150 gram)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 29.0, 2.4, 0.0, 3.08, 1.65, 1.5)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kabak (orta boy-150 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Ananas Çayı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Ananas Çayı', NULL, 'ml', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Ananas Çayı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çubuk Tarçın (5 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çubuk Tarçın (5 gram)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 14.0, 0.0, 0.0, 2.8, 0.0, 1.3)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çubuk Tarçın (5 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Dereotu( 1 porsiyon- 40 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Dereotu( 1 porsiyon- 40 gram)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 7.0, 0.5, 0.1, 1.12, 2.12, 10.8)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Dereotu( 1 porsiyon- 40 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Mısır gevreği (Corn flakes
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Mısır gevreği (Corn flakes', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 400.0, 7.0, 2.0, 81.0, 5.0, 1.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Mısır gevreği (Corn flakes')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Ödem Atıcı Çay
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Ödem Atıcı Çay', NULL, 'ml', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Ödem Atıcı Çay')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Corn Flakes (Kranky-Şok marketteki)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Corn Flakes (Kranky-Şok marketteki)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 369.0, 7.0, 1.0, 83.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Corn Flakes (Kranky-Şok marketteki)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Muz
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Muz', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 100.0, 1.0, 0.0, 23.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Muz')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Lor Peyniri ( Sürülebilir)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Lor Peyniri ( Sürülebilir)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 181.0, 10.0, 13.0, 2.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Lor Peyniri ( Sürülebilir)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Glutensiz yulaf ezmesi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Glutensiz yulaf ezmesi', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 389.0, 17.0, 7.0, 66.0, 11.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Glutensiz yulaf ezmesi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Glutensiz Ekmek
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Glutensiz Ekmek', NULL, 'Dilim', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 54.0, 1.51, 0.38, 11.14, 1.62, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Glutensiz Ekmek')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kayısı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kayısı', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 14.0, 0.4, 0.0, 3.34, 0.6, 0.3)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kayısı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Şeftali (1 orta boy- 120 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Şeftali (1 orta boy- 120 gram)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 47.0, 1.09, 0.0, 11.45, 1.8, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Şeftali (1 orta boy- 120 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Pre Workout
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Pre Workout', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Pre Workout')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- greyfurt
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('greyfurt', NULL, 'Yarım adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 50.0, 0.3, 0.1, 4.5, 0.3, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'greyfurt')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- CARNİFLAME YAĞ YAKICI
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('CARNİFLAME YAĞ YAKICI', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 12.0, 3.0, 1.0, 1.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'CARNİFLAME YAĞ YAKICI')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Fırın Sebze (100 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Fırın Sebze (100 gram)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 55.0, 1.57, 2.5, 6.19, 2.4, 236.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Fırın Sebze (100 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Konserve Çoban Kebabı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Konserve Çoban Kebabı', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 158.0, 9.5, 10.0, 5.0, 0.7, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Konserve Çoban Kebabı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Konserve Nohutlu Pirinç Pilavı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Konserve Nohutlu Pirinç Pilavı', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 215.0, 3.0, 7.0, 33.0, 0.9, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Konserve Nohutlu Pirinç Pilavı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Konserve Tavuk Güveç
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Konserve Tavuk Güveç', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 106.0, 11.4, 5.7, 1.9, 1.2, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Konserve Tavuk Güveç')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Semizotu ( 124 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Semizotu ( 124 gram)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 27.0, 3.27, 0.0, 2.19, 1.97, 50.84)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Semizotu ( 124 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Mor Lahana ( çeyrek-80 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Mor Lahana ( çeyrek-80 gram)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 29.0, 0.42, 0.17, 5.59, 1.57, 13.6)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Mor Lahana ( çeyrek-80 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Konserve Arpa Şehriyeli Pirinç Pilavı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Konserve Arpa Şehriyeli Pirinç Pilavı', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 215.0, 3.0, 7.0, 33.5, 0.9, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Konserve Arpa Şehriyeli Pirinç Pilavı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Uniq2go Protein Bar
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Uniq2go Protein Bar', NULL, 'Paket', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 160.0, 10.0, 1.4, 25.0, 6.4, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Uniq2go Protein Bar')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- OAT CREAM
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('OAT CREAM', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 133.0, 11.4, 2.8, 18.9, 4.2, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'OAT CREAM')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Collagen
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Collagen', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 42.0, 9.0, 0.0, 0.0, 0.0, 100.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Collagen')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- DR.PAN SWEET FLAVOR ( salted caramel  )
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('DR.PAN SWEET FLAVOR ( salted caramel  )', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'DR.PAN SWEET FLAVOR ( salted caramel  )')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- DR.PAN SWEET FLAVOR ( Strawberry  )
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('DR.PAN SWEET FLAVOR ( Strawberry  )', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'DR.PAN SWEET FLAVOR ( Strawberry  )')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- DR.PAN SWEET FLAVOR ( Cookies
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('DR.PAN SWEET FLAVOR ( Cookies', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'DR.PAN SWEET FLAVOR ( Cookies')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Nektari (1 orta boy-110 g)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Nektari (1 orta boy-110 g)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 47.0, 0.22, 0.39, 9.48, 2.28, 3.3)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Nektari (1 orta boy-110 g)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Taze nane (5 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Taze nane (5 gr)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 2.0, 0.17, 0.04, 0.08, 0.33, 0.25)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Taze nane (5 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- konserve mısır (60 g)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('konserve mısır (60 g)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 62.0, 1.62, 0.48, 12.6, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'konserve mısır (60 g)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- sarı üzüm (100 g)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('sarı üzüm (100 g)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 69.0, 0.72, 0.16, 18.1, 0.9, 2.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'sarı üzüm (100 g)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Oxandrolone ( 10 mg)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Oxandrolone ( 10 mg)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Oxandrolone ( 10 mg)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Winstrol Tablet (25 mg)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Winstrol Tablet (25 mg)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Winstrol Tablet (25 mg)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- nektari (yarım adet-55 g)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('nektari (yarım adet-55 g)', NULL, 'Yarım adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 23.5, 0.11, 0.2, 18.96, 1.14, 1.65)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'nektari (yarım adet-55 g)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- whey protein- 1/2 servis
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('whey protein- 1/2 servis', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 59.62, 11.25, 1.14, 0.5, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'whey protein- 1/2 servis')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- tofu (1 porsiyon-30g)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('tofu (1 porsiyon-30g)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 44.0, 3.8, 3.0, 1.32, 0.18, 0.6)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'tofu (1 porsiyon-30g)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kiraz saplı çay
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kiraz saplı çay', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kiraz saplı çay')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Üzüm (1/2 porsiyon-75 g)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Üzüm (1/2 porsiyon-75 g)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 52.0, 0.54, 0.12, 13.58, 0.68, 1.5)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Üzüm (1/2 porsiyon-75 g)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Ispanak (150 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Ispanak (150 gram)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 25.55, 3.8, 0.5, 0.1, 3.9, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Ispanak (150 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Armut (1 küçük boy-150 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Armut (1 küçük boy-150 gram)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 86.0, 0.54, 0.21, 22.85, 4.65, 1.5)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Armut (1 küçük boy-150 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Zeytin Yağı (5 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Zeytin Yağı (5 gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 44.0, 0.0, 5.0, 0.01, 0.0, 0.1)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Zeytin Yağı (5 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Propolis
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Propolis', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Propolis')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Şeftali (1/2 porsiyon-60 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Şeftali (1/2 porsiyon-60 gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 23.0, 0.55, 0.15, 5.72, 0.9, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Şeftali (1/2 porsiyon-60 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- SSN BCAA THERMO KİCK
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('SSN BCAA THERMO KİCK', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 51.0, 9.5, 0.07, 3.0, 0.0, 0.01)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'SSN BCAA THERMO KİCK')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Femara
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Femara', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Femara')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Armut (75 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Armut (75 gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 43.0, 0.27, 0.11, 11.42, 2.33, 0.75)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Armut (75 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Mandalina (1 porsiyon-150 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Mandalina (1 porsiyon-150 gr)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 80.0, 1.22, 0.47, 20.51, 2.7, 3.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Mandalina (1 porsiyon-150 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Portakal (1/2 porsiyon-110 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Portakal (1/2 porsiyon-110 gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 51.0, 0.77, 0.23, 12.69, 2.64, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Portakal (1/2 porsiyon-110 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kereviz (1 porsiyon-100 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kereviz (1 porsiyon-100 gr)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 42.0, 1.5, 0.3, 9.2, 1.8, 100.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kereviz (1 porsiyon-100 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- kivi (75 gr-1/2 porsiyon)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('kivi (75 gr-1/2 porsiyon)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 46.0, 0.11, 0.39, 11.0, 2.25, 2.25)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'kivi (75 gr-1/2 porsiyon)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kestane (1/4 porsiyon-15 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kestane (1/4 porsiyon-15 gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 30.0, 0.6, 0.15, 6.6, 0.9, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kestane (1/4 porsiyon-15 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- SSN MASS REFUEL
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('SSN MASS REFUEL', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 413.75, 20.0, 1.0, 82.0, 0.0, 0.36)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'SSN MASS REFUEL')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tereyağı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tereyağı', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 700.0, 10.0, 81.0, 0.0, 0.0, 11.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tereyağı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- NEMOGO
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('NEMOGO', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'NEMOGO')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Prolex probiyotik
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Prolex probiyotik', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Prolex probiyotik')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Mandalina ( 1 küçük boy-70 g)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Mandalina ( 1 küçük boy-70 g)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 37.0, 0.0, 0.0, 9.3, 1.26, 1.4)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Mandalina ( 1 küçük boy-70 g)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gainer Pro (Biogain Aromasız)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gainer Pro (Biogain Aromasız)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 389.0, 18.0, 2.0, 75.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gainer Pro (Biogain Aromasız)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- B Kompleks Vitamin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('B Kompleks Vitamin', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'B Kompleks Vitamin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Patlıcan (orta boy-200 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Patlıcan (orta boy-200 gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 34.0, 2.48, 0.36, 4.98, 5.64, 6.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Patlıcan (orta boy-200 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Pirinç Unu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Pirinç Unu', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 400.0, 6.0, 1.0, 80.0, 2.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Pirinç Unu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- LEDAPHARMA KOLLAJEN
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('LEDAPHARMA KOLLAJEN', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'LEDAPHARMA KOLLAJEN')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tavuk Göğüs - derisiz (ızgara veya sebzelerle sote yapılabilir)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tavuk Göğüs - derisiz (ızgara veya sebzelerle sote yapılabilir)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 121.0, 21.7, 3.78, 0.0, 0.0, 38.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tavuk Göğüs - derisiz (ızgara veya sebzelerle sote yapılabilir)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Bigjoy Sports BIGMASS Gainer
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Bigjoy Sports BIGMASS Gainer', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 396.0, 19.6, 0.72, 77.6, 0.3, 0.39)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Bigjoy Sports BIGMASS Gainer')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Bigjoy Sports BIG2 Bcaa   Glutamine
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Bigjoy Sports BIG2 Bcaa   Glutamine', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 8.0, 0.0, 0.0, 2.1, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Bigjoy Sports BIG2 Bcaa   Glutamine')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST NUTRİTİON WHEY PROTEİN- 1 servis 36 gram
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST NUTRİTİON WHEY PROTEİN- 1 servis 36 gram', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 143.6, 26.5, 2.4, 3.8, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST NUTRİTİON WHEY PROTEİN- 1 servis 36 gram')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- SANMARK VİTAMİN-C ( Çiğnenebilir)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('SANMARK VİTAMİN-C ( Çiğnenebilir)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'SANMARK VİTAMİN-C ( Çiğnenebilir)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- TRİBU 90 ( Tribulus)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('TRİBU 90 ( Tribulus)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'TRİBU 90 ( Tribulus)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- CENTRUVİT MULTİVİTAMİN
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('CENTRUVİT MULTİVİTAMİN', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'CENTRUVİT MULTİVİTAMİN')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- SSN COMMAND QUADRO VİTAMİN-MİNERAL
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('SSN COMMAND QUADRO VİTAMİN-MİNERAL', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'SSN COMMAND QUADRO VİTAMİN-MİNERAL')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- zma ( Bigjoy)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('zma ( Bigjoy)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'zma ( Bigjoy)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- LİVTAB DEVE DİKENİ MİLK THİSTLE VE ENGİNAR EKSTRESİ
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('LİVTAB DEVE DİKENİ MİLK THİSTLE VE ENGİNAR EKSTRESİ', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'LİVTAB DEVE DİKENİ MİLK THİSTLE VE ENGİNAR EKSTRESİ')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BİGJOY SPORTS THERMONATOR KARNİTİN
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BİGJOY SPORTS THERMONATOR KARNİTİN', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BİGJOY SPORTS THERMONATOR KARNİTİN')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- OLİMP R-WEİLER SHOT
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('OLİMP R-WEİLER SHOT', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'OLİMP R-WEİLER SHOT')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- OLİMP THERMO SPEED XTREME
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('OLİMP THERMO SPEED XTREME', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'OLİMP THERMO SPEED XTREME')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- THERMONATOR RİPPED
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('THERMONATOR RİPPED', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'THERMONATOR RİPPED')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- TORQ CLA
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('TORQ CLA', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'TORQ CLA')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BİGJOY SPORTS CAFFEİNE PLUS
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BİGJOY SPORTS CAFFEİNE PLUS', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BİGJOY SPORTS CAFFEİNE PLUS')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gainer Big Mass   GH FACTORS (1 servis-2 ölçek)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gainer Big Mass   GH FACTORS (1 servis-2 ölçek)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 396.0, 19.6, 0.7, 78.8, 0.3, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gainer Big Mass   GH FACTORS (1 servis-2 ölçek)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gainer West Nutrition - 1 servis (4 ölçek- 100 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gainer West Nutrition - 1 servis (4 ölçek- 100 gram)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 398.0, 16.9, 0.0, 79.3, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gainer West Nutrition - 1 servis (4 ölçek- 100 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gainer Nutrend Mass Gold 1 servis - (3,5 ölçek - 100 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gainer Nutrend Mass Gold 1 servis - (3,5 ölçek - 100 gram)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 382.0, 26.0, 2.5, 64.5, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gainer Nutrend Mass Gold 1 servis - (3,5 ölçek - 100 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gainer SSN MASS REFUEL 1 servis- 4 ölçek (110 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gainer SSN MASS REFUEL 1 servis- 4 ölçek (110 gram)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 413.7, 20.0, 0.0, 82.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gainer SSN MASS REFUEL 1 servis- 4 ölçek (110 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Zma Arginine (1 kapsül)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Zma Arginine (1 kapsül)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 2.0, 0.6, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Zma Arginine (1 kapsül)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kuşkonmaz (pişmiş-150 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kuşkonmaz (pişmiş-150 gram)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 33.0, 3.6, 0.33, 6.17, 3.0, 21.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kuşkonmaz (pişmiş-150 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Gainer Big Mass GH FACTORS (1/2servis-1 ölçek)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Gainer Big Mass GH FACTORS (1/2servis-1 ölçek)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 198.0, 8.5, 0.03, 39.4, 0.01, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Gainer Big Mass GH FACTORS (1/2servis-1 ölçek)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BIOGAİN WHEY PROTEİN (1 şase-30 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BIOGAİN WHEY PROTEİN (1 şase-30 gram)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 119.8, 24.8, 2.3, 2.1, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BIOGAİN WHEY PROTEİN (1 şase-30 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- SSN COMMAND QUADRO WHEY (1 ölçek-30 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('SSN COMMAND QUADRO WHEY (1 ölçek-30 gram)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 116.0, 23.0, 1.8, 1.35, 1.38, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'SSN COMMAND QUADRO WHEY (1 ölçek-30 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Torq BCAA
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Torq BCAA', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Torq BCAA')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BİG JOY BCAABİG (1 ölçek-18.4 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BİG JOY BCAABİG (1 ölçek-18.4 gram)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BİG JOY BCAABİG (1 ölçek-18.4 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BİG JOY BİG2 BCAA   GLUTAMİNE
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BİG JOY BİG2 BCAA   GLUTAMİNE', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BİG JOY BİG2 BCAA   GLUTAMİNE')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BIOGAIN GLUTAMİN
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BIOGAIN GLUTAMİN', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BIOGAIN GLUTAMİN')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST L-GLUTAMİN
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST L-GLUTAMİN', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST L-GLUTAMİN')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- MARİNCAP (Omega 3)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('MARİNCAP (Omega 3)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'MARİNCAP (Omega 3)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- SSN COMMAND QUADRO VİTAMİN-MİNERAL
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('SSN COMMAND QUADRO VİTAMİN-MİNERAL', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'SSN COMMAND QUADRO VİTAMİN-MİNERAL')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BİGJOY SPORTS CLABİG
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BİGJOY SPORTS CLABİG', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BİGJOY SPORTS CLABİG')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- OLİMP R-WEİLER SHOT
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('OLİMP R-WEİLER SHOT', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'OLİMP R-WEİLER SHOT')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- OLİMP KNOCKOUT 2.0 PRE-WORKOUT
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('OLİMP KNOCKOUT 2.0 PRE-WORKOUT', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'OLİMP KNOCKOUT 2.0 PRE-WORKOUT')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- OLİMP TRİBUSTERON
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('OLİMP TRİBUSTERON', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'OLİMP TRİBUSTERON')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- TRİBU90 TRİBULUS
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('TRİBU90 TRİBULUS', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'TRİBU90 TRİBULUS')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- NUTREND MASS GAİN (3.5 ölçek-100 gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('NUTREND MASS GAİN (3.5 ölçek-100 gram)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 382.0, 26.0, 2.2, 64.5, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'NUTREND MASS GAİN (3.5 ölçek-100 gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BİGJOY SPORTS ZMA
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BİGJOY SPORTS ZMA', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BİGJOY SPORTS ZMA')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BİG JOY PRE-DATOR
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BİG JOY PRE-DATOR', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BİG JOY PRE-DATOR')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Mezgit Balığı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Mezgit Balığı', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 100.0, 15.0, 1.0, 0.0, 0.0, 124.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Mezgit Balığı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Bulgur
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Bulgur', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 300.0, 9.0, 1.0, 69.0, 10.0, 5.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Bulgur')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Trabzon Hurması (orta boy-80 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Trabzon Hurması (orta boy-80 gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 58.0, 0.31, 0.06, 12.05, 4.05, 1.6)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Trabzon Hurması (orta boy-80 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Nar
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Nar', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 80.0, 2.0, 0.0, 20.0, 4.0, 236.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Nar')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Siyah Çay
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Siyah Çay', NULL, 'Çay Bardağı', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Siyah Çay')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Pirinç
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Pirinç', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 360.0, 7.0, 0.0, 79.0, 0.0, 80.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Pirinç')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Cabaser 0.5 Mg (14  Günde 1 Tablet
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Cabaser 0.5 Mg (14  Günde 1 Tablet', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Cabaser 0.5 Mg (14  Günde 1 Tablet')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Taurin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Taurin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Taurin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- KALSİYUM 600 mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('KALSİYUM 600 mg', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'KALSİYUM 600 mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- DEMİR
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('DEMİR', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'DEMİR')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- ÇİNKO
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('ÇİNKO', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'ÇİNKO')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Taze fasulye (1/2 porsiyon-75 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Taze fasulye (1/2 porsiyon-75 gr)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 23.0, 1.37, 0.17, 5.23, 2.03, 4.5)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Taze fasulye (1/2 porsiyon-75 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- yumurta sarısı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('yumurta sarısı', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 64.0, 3.17, 5.31, 0.06, 0.0, 9.6)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'yumurta sarısı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Bigjoy Sports BIG MASS Gainer (1/2 servis)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Bigjoy Sports BIG MASS Gainer (1/2 servis)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 198.0, 9.8, 0.36, 38.8, 0.15, 0.19)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Bigjoy Sports BIG MASS Gainer (1/2 servis)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Mısır ve Pirinç Patlağı ( Burch)-1 adet 8 gr
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Mısır ve Pirinç Patlağı ( Burch)-1 adet 8 gr', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 30.75, 0.6, 0.1, 6.8, 0.2, 0.4)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Mısır ve Pirinç Patlağı ( Burch)-1 adet 8 gr')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Brüksel Lahanası (150 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Brüksel Lahanası (150 gr)', NULL, 'Porsiyon', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 54.0, 6.68, 0.51, 4.93, 6.6, 15.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Brüksel Lahanası (150 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- folik asit
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('folik asit', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'folik asit')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Biogain carniburn karnitin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Biogain carniburn karnitin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Biogain carniburn karnitin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Badem ezmesi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Badem ezmesi', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 600.0, 10.0, 60.0, 20.0, 3.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Badem ezmesi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Biotin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Biotin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Biotin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Jelibon (10 gr )
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Jelibon (10 gr )', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 34.0, 0.65, 0.01, 7.59, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Jelibon (10 gr )')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Haşlama Mısır
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Haşlama Mısır', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 100.0, 3.0, 2.0, 21.0, 2.0, 2.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Haşlama Mısır')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Aspirin 1 tablet
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Aspirin 1 tablet', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Aspirin 1 tablet')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST bcaa glutamine
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST bcaa glutamine', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST bcaa glutamine')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST bcaa
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST bcaa', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST bcaa')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST kreatin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST kreatin', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST kreatin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST l-arjinin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST l-arjinin', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST l-arjinin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST glutamin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST glutamin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST glutamin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST l-karnitin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST l-karnitin', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST l-karnitin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST taurin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST taurin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST taurin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST proteinli mocha
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST proteinli mocha', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST proteinli mocha')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST protein bar (50gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST protein bar (50gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 196.0, 15.0, 2.6, 19.6, 3.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST protein bar (50gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- WEST livtab
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('WEST livtab', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'WEST livtab')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- FİTNUT YERFISTIĞI YAĞI (1 yemek kaşığı-14 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('FİTNUT YERFISTIĞI YAĞI (1 yemek kaşığı-14 gr)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 850.0, 0.0, 100.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'FİTNUT YERFISTIĞI YAĞI (1 yemek kaşığı-14 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Zma Arginine
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Zma Arginine', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Zma Arginine')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Dana Kıyma (pişmiş)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Dana Kıyma (pişmiş)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 200.0, 28.0, 12.0, 1.0, 0.0, 40.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Dana Kıyma (pişmiş)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tam buğdaylı ekmek (1 ince dilim-25 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tam buğdaylı ekmek (1 ince dilim-25 gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 54.0, 2.1, 0.4, 11.2, 1.67, 113.17)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tam buğdaylı ekmek (1 ince dilim-25 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Nox2
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Nox2', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Nox2')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Pancar Suyu (1 sb-200 ml)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Pancar Suyu (1 sb-200 ml)', NULL, 'Su Bardağı', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 88.0, 3.36, 0.36, 19.92, 4.0, 154.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Pancar Suyu (1 sb-200 ml)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Arimidex (Gün Aşırı) 1 adet
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Arimidex (Gün Aşırı) 1 adet', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Arimidex (Gün Aşırı) 1 adet')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sade Quark
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sade Quark', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 97.0, 9.0, 5.0, 5.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sade Quark')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çinko 15 mg (leda)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çinko 15 mg (leda)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çinko 15 mg (leda)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tam Buğdaylı Lavaş
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tam Buğdaylı Lavaş', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 300.0, 9.0, 8.0, 48.0, 5.0, 2.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tam Buğdaylı Lavaş')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- AOL
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('AOL', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'AOL')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- C Vitamini 1000 mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('C Vitamini 1000 mg', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'C Vitamini 1000 mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- L-Carnitine
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('L-Carnitine', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'L-Carnitine')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Enginar (1 orta boy-100 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Enginar (1 orta boy-100 gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 47.0, 3.27, 0.15, 10.51, 5.4, 94.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Enginar (1 orta boy-100 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Magnezyum Sitrat
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Magnezyum Sitrat', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Magnezyum Sitrat')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- MALTODEXTRIN (100 Gram)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('MALTODEXTRIN (100 Gram)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 38000.0, 0.0, 0.0, 9500.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'MALTODEXTRIN (100 Gram)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Bromelain
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Bromelain', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Bromelain')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Nutraxin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Nutraxin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Nutraxin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Magnezyum malat
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Magnezyum malat', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Magnezyum malat')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kırmızı erik (1 orta boy-35 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kırmızı erik (1 orta boy-35 gr)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 19.0, 0.06, 0.18, 3.84, 0.77, 1.05)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kırmızı erik (1 orta boy-35 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Lor Peyniri (yağı düşük)250gr
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Lor Peyniri (yağı düşük)250gr', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 180.0, 25.85, 0.73, 16.65, 0.0, 930.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Lor Peyniri (yağı düşük)250gr')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Bisküvili Protein Tozu( prot. ocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Bisküvili Protein Tozu( prot. ocean)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 416.0, 73.6, 6.8, 14.4, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Bisküvili Protein Tozu( prot. ocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- HIQ PRO V-BUILDER (50 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('HIQ PRO V-BUILDER (50 gr)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 198.0, 22.0, 1.5, 24.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'HIQ PRO V-BUILDER (50 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Detoksfit (Tablet)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Detoksfit (Tablet)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Detoksfit (Tablet)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tuz ( İyotlu Sofra Tuzu )
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tuz ( İyotlu Sofra Tuzu )', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tuz ( İyotlu Sofra Tuzu )')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yeşil Çay Extresi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yeşil Çay Extresi', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yeşil Çay Extresi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Guarana Extresi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Guarana Extresi', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Guarana Extresi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Melatonin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Melatonin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Melatonin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Selenyum
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Selenyum', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Selenyum')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tyrosin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tyrosin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tyrosin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Nohut
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Nohut', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 360.0, 20.5, 4.8, 61.0, 5.0, 26.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Nohut')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Keçiboynuzu unu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Keçiboynuzu unu', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 222.0, 4.62, 0.65, 88.88, 39.8, 35.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Keçiboynuzu unu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Çiğ Kaju
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Çiğ Kaju', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 11.4, 0.3, 0.92, 0.66, 0.06, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Çiğ Kaju')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yeşil Mercimek (çiğ)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yeşil Mercimek (çiğ)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 299.0, 23.0, 0.92, 36.62, 25.99, 13.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yeşil Mercimek (çiğ)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Carbofuel
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Carbofuel', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Carbofuel')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- t-prime
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('t-prime', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 't-prime')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Whey protein (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Whey protein (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 104.0, 18.4, 1.7, 3.6, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Whey protein (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- collagen (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('collagen (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'collagen (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Pre-workout supreme (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Pre-workout supreme (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Pre-workout supreme (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BCAA 4.1.1 (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BCAA 4.1.1 (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BCAA 4.1.1 (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Glutamine  (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Glutamine  (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Glutamine  (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- creatine (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('creatine (proteinocean)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'creatine (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Arginine  (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Arginine  (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Arginine  (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- L-carnitine (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('L-carnitine (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'L-carnitine (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- CLA (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('CLA (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'CLA (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Mass Gainer (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Mass Gainer (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 383.0, 13.7, 1.3, 79.2, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Mass Gainer (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- RED Detox (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('RED Detox (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'RED Detox (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Maltodetrin 100g (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Maltodetrin 100g (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 390.0, 0.0, 0.0, 97.5, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Maltodetrin 100g (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- prebiotics (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('prebiotics (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'prebiotics (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Vitamin D3K2 1000IU (herbina)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Vitamin D3K2 1000IU (herbina)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Vitamin D3K2 1000IU (herbina)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- OMEGA 3 (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('OMEGA 3 (proteinocean)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'OMEGA 3 (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Vitamin D3 (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Vitamin D3 (proteinocean)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Vitamin D3 (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- ZMA (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('ZMA (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'ZMA (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- ESTER C (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('ESTER C (proteinocean)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'ESTER C (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Multivitamin (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Multivitamin (proteinocean)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Multivitamin (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Cream of Rice (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Cream of Rice (proteinocean)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 348.0, 9.2, 0.0, 75.8, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Cream of Rice (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Hyaluronik asit
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Hyaluronik asit', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Hyaluronik asit')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Cacık (100 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Cacık (100 gr)', NULL, 'Kase (Küçük)', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 41.0, 2.03, 2.12, 3.15, 0.24, 271.55)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Cacık (100 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Carb Blocker (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Carb Blocker (proteinocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Carb Blocker (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Hunger Buster (proteinocean Flava)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Hunger Buster (proteinocean Flava)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Hunger Buster (proteinocean Flava)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Maltodekstrin (50 GRAM)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Maltodekstrin (50 GRAM)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 19000.0, 0.0, 0.0, 4750.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Maltodekstrin (50 GRAM)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- CR7 HERBALİFE SPORCU İÇECEĞİ
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('CR7 HERBALİFE SPORCU İÇECEĞİ', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 97.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'CR7 HERBALİFE SPORCU İÇECEĞİ')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Altınbaşak Çörekotlu ve Kinoalı kraker (40 gr-1 paket)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Altınbaşak Çörekotlu ve Kinoalı kraker (40 gr-1 paket)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 164.0, 4.0, 4.3, 25.5, 3.4, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Altınbaşak Çörekotlu ve Kinoalı kraker (40 gr-1 paket)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Dextrose (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Dextrose (proteinocean)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 365.0, 0.0, 0.0, 92.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Dextrose (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- YOHIMBE
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('YOHIMBE', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'YOHIMBE')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- GAMER HACK(protein ocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('GAMER HACK(protein ocean)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 13.0, 0.0, 0.0, 3.3, 0.0, 0.1)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'GAMER HACK(protein ocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Palamut
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Palamut', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 216.0, 20.16, 15.07, 0.0, 0.0, 43.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Palamut')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Reçel (5 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Reçel (5 gr)', NULL, 'Tatlı Kaşığı', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 14.0, 0.01, 0.01, 3.42, 0.04, 0.05)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Reçel (5 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- ANİMAL PACK
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('ANİMAL PACK', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'ANİMAL PACK')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- C VİTAMİNİ 500mg (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('C VİTAMİNİ 500mg (proteinocean)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'C VİTAMİNİ 500mg (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- D VİTAMİNİ 1000IU (proteinocean)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('D VİTAMİNİ 1000IU (proteinocean)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'D VİTAMİNİ 1000IU (proteinocean)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Termojenik
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Termojenik', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Termojenik')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Ihlamur Çayı
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Ihlamur Çayı', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Ihlamur Çayı')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- C VİTAMİNİ 500mg (sanmarco)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('C VİTAMİNİ 500mg (sanmarco)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'C VİTAMİNİ 500mg (sanmarco)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- OMEGA 3 1000mg (herbina)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('OMEGA 3 1000mg (herbina)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'OMEGA 3 1000mg (herbina)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Vitamin D3K2 1000IU (wiselab)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Vitamin D3K2 1000IU (wiselab)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Vitamin D3K2 1000IU (wiselab)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Vitamin D3 (leda)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Vitamin D3 (leda)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Vitamin D3 (leda)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Multivitamin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Multivitamin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Multivitamin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Omega 3 1000 mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Omega 3 1000 mg', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 9.0, 0.0, 1.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Omega 3 1000 mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- çinko 15 mg
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('çinko 15 mg', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'çinko 15 mg')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Spirulina
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Spirulina', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Spirulina')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BIO GAİN aromalı tatlandırıcı ( cookie)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BIO GAİN aromalı tatlandırıcı ( cookie)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BIO GAİN aromalı tatlandırıcı ( cookie)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BIO GAİN aromalı tatlandırıcı ( çikolata )
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BIO GAİN aromalı tatlandırıcı ( çikolata )', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BIO GAİN aromalı tatlandırıcı ( çikolata )')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BIO GAİN aromalı tatlandırıcı ( salted caramel )
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BIO GAİN aromalı tatlandırıcı ( salted caramel )', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BIO GAİN aromalı tatlandırıcı ( salted caramel )')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Şekersiz Fıstık Ezmesi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Şekersiz Fıstık Ezmesi', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 645.0, 29.0, 56.0, 6.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Şekersiz Fıstık Ezmesi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Yulaf Ezmesi Organik (dahafitol)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Yulaf Ezmesi Organik (dahafitol)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 370.0, 12.53, 1.0, 63.29, 5.43, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Yulaf Ezmesi Organik (dahafitol)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Pirinç Patlağı Sade (dahafitol)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Pirinç Patlağı Sade (dahafitol)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 26.92, 0.52, 0.0, 5.96, 0.11, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Pirinç Patlağı Sade (dahafitol)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Karabuğday Patlağı (dahafitol)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Karabuğday Patlağı (dahafitol)', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 26.38, 1.02, 0.26, 5.5, 0.77, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Karabuğday Patlağı (dahafitol)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Konserve Kavurma
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Konserve Kavurma', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 358.0, 20.0, 30.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Konserve Kavurma')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Enginar Suyu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Enginar Suyu', NULL, 'Su Bardağı', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Enginar Suyu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Kekik Suyu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Kekik Suyu', NULL, 'Su Bardağı', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Kekik Suyu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- FitNut Fıstık Ezmesi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('FitNut Fıstık Ezmesi', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 579.0, 29.5, 46.0, 11.6, 8.5, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'FitNut Fıstık Ezmesi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- king size beast mode
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('king size beast mode', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'king size beast mode')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Olimp Whey İsolate (1 servis 30 gr)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Olimp Whey İsolate (1 servis 30 gr)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 106.0, 26.0, 0.5, 0.5, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Olimp Whey İsolate (1 servis 30 gr)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Hindistan Cevizi (toz)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Hindistan Cevizi (toz)', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 360.0, 0.0, 40.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Hindistan Cevizi (toz)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- esansiyel amino asit (EAA-PROTEİN OCEAN)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('esansiyel amino asit (EAA-PROTEİN OCEAN)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'esansiyel amino asit (EAA-PROTEİN OCEAN)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- ssn comand quadro whey
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('ssn comand quadro whey', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 116.0, 23.0, 1.89, 1.35, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'ssn comand quadro whey')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- herbina cla
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('herbina cla', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'herbina cla')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Marul
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Marul', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Marul')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Göbek Salata
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Göbek Salata', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Göbek Salata')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Hindistan Cevizi
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Hindistan Cevizi', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 340.0, 4.0, 37.0, 5.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Hindistan Cevizi')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- SAN MARCO BCAA (TROPİCAL , VİŞNE)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('SAN MARCO BCAA (TROPİCAL , VİŞNE)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'SAN MARCO BCAA (TROPİCAL , VİŞNE)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- HERBİNA ZMA
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('HERBİNA ZMA', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'HERBİNA ZMA')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- BIOGAIN CARNIBURN YAĞ YAKICI
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('BIOGAIN CARNIBURN YAĞ YAKICI', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'BIOGAIN CARNIBURN YAĞ YAKICI')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Aromasin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Aromasin', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Aromasin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- SSN GLUTAMİNE
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('SSN GLUTAMİNE', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'SSN GLUTAMİNE')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Sebze Çorbası
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Sebze Çorbası', NULL, 'Kase (Normal)', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 70.0, 1.0, 1.68, 6.0, 0.9, 0.04)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Sebze Çorbası')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- İsole Whey Protein
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('İsole Whey Protein', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 119.24, 22.5, 2.28, 1.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'İsole Whey Protein')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Curcumin
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Curcumin', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Curcumin')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Primeose Oil Capsül
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Primeose Oil Capsül', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Primeose Oil Capsül')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Soya Protein Tozu (proteinocn)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Soya Protein Tozu (proteinocn)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 89.0, 21.95, 0.0, 0.4, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Soya Protein Tozu (proteinocn)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Protein Ocean LIVER / (1 servis - 2 kapsül)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Protein Ocean LIVER / (1 servis - 2 kapsül)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Protein Ocean LIVER / (1 servis - 2 kapsül)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Protein Ocean KIDNEY / (1 servis - 2 tablet)
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Protein Ocean KIDNEY / (1 servis - 2 tablet)', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Protein Ocean KIDNEY / (1 servis - 2 tablet)')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- PUMP STIM FREE / Kafeinsiz PreWorkout
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('PUMP STIM FREE / Kafeinsiz PreWorkout', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'PUMP STIM FREE / Kafeinsiz PreWorkout')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- ARIMIDEX GÜNDE 1 ADET
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('ARIMIDEX GÜNDE 1 ADET', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'ARIMIDEX GÜNDE 1 ADET')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Ashwagandha
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Ashwagandha', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Ashwagandha')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Tongkat Ali
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Tongkat Ali', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Tongkat Ali')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Karaciğer Koruyucu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Karaciğer Koruyucu', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Karaciğer Koruyucu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Böbrek Koruyucu
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Böbrek Koruyucu', NULL, 'adet', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Böbrek Koruyucu')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Deep Sleep - Protein Ocean
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Deep Sleep - Protein Ocean', NULL, 'Servis', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Deep Sleep - Protein Ocean')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Whey Isolate Protein
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Whey Isolate Protein', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 300.0, 90.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Whey Isolate Protein')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

  -- Glutamine
  INSERT INTO food_items (name_en, piece_weight_g, serving_unit, is_featured, source)
  VALUES ('Glutamine', NULL, 'g', TRUE, 'begreens')
  ON CONFLICT DO NOTHING
  RETURNING id INTO fid;
  IF fid IS NOT NULL THEN
    INSERT INTO food_nutrients_100g (food_id, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sodium_mg)
    VALUES (fid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    ON CONFLICT (food_id) DO NOTHING;
    INSERT INTO food_localization_tr (food_id, name_tr)
    VALUES (fid, 'Glutamine')
    ON CONFLICT (food_id) DO NOTHING;
  END IF;

END $$;