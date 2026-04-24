-- ═══════════════════════════════════════════════════════════
-- FithubPoint Demo Data — sunum ve ekran görüntüsü için
-- Şifre: FitHub2026Demo!
-- Çalıştır: psql $DATABASE_URL -f seeds/demo_data.sql
-- ═══════════════════════════════════════════════════════════

-- Bcrypt hash for "FitHub2026Demo!"
-- $2b$12$k.Q0iK5WIW1LzJ.rIM0jaeDh3zmeaG1PwZajLt6kWdezHkg84z4gW

-- ────────────────────────────────────────────
-- 1. MOCK KOÇLAR (3 adet)
-- ────────────────────────────────────────────

-- Koç 1: Elif Demir (Kadın, Women Fitness)
INSERT INTO users (email, password_hash, full_name, role, phone_number, timezone, profile_photo_url, created_at, updated_at)
VALUES (
  'elif.demir@fithub.demo',
  '$2b$12$k.Q0iK5WIW1LzJ.rIM0jaeDh3zmeaG1PwZajLt6kWdezHkg84z4gW',
  'Elif Demir',
  'coach',
  '+905551110001',
  'Europe/Istanbul',
  'https://images.unsplash.com/photo-1594381898411-846e7d193883?w=400&h=400&fit=crop&crop=face',
  NOW() - INTERVAL '6 months',
  NOW()
) ON CONFLICT (email) DO NOTHING;

INSERT INTO coaches (user_id, bio, photo_url, specialties, title, instagram, twitter, linkedin, website, is_active, rating, rating_count, photos, certificates, referral_code)
SELECT u.id,
  'ACE sertifikalı kadın fitness uzmanı. 8 yıllık deneyimle 500+ kadına dönüşüm koçluğu yaptım. Yağ yakma, toparlanma ve sürdürülebilir beslenme konusunda uzmanım. Seninle birlikte güçlü ve sağlıklı bir vücut inşa edeceğiz.',
  'https://images.unsplash.com/photo-1594381898411-846e7d193883?w=800&h=800&fit=crop&crop=face',
  ARRAY['Yağ Yakma', 'Fonksiyonel Antrenman', 'Pilates', 'Beslenme', 'Kadın Fitness'],
  'ACE Sertifikalı Kadın Fitness Uzmanı',
  '@elifdemir.fit',
  '@elif_fit',
  'in/elifdemir',
  'https://elifdemir.fit',
  TRUE,
  4.9,
  127,
  ARRAY[
    'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600',
    'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=600',
    'https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=600'
  ],
  ARRAY[
    'https://images.unsplash.com/photo-1523050854058-8df90110c476?w=400',
    'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=400'
  ],
  'ELIF25'
FROM users u WHERE u.email = 'elif.demir@fithub.demo'
ON CONFLICT DO NOTHING;

-- Elif Demir paketleri
INSERT INTO coach_packages (coach_user_id, name, description, duration_days, price, discount_percentage, is_active, services)
SELECT u.id,
  '3 Aylık Dönüşüm',
  'Kişiye özel antrenman + beslenme programı, haftalık görüntülü görüşme, 7/24 mesajlaşma. Hedefine en hızlı şekilde ulaş.',
  90, 4500, 0, TRUE,
  ARRAY['Kişiye Özel Antrenman', 'Beslenme Planı', 'Görüntülü Görüşme', '7/24 Sohbet', 'Haftalık Kontrol', 'İlerleme Takibi']
FROM users u WHERE u.email = 'elif.demir@fithub.demo'
ON CONFLICT DO NOTHING;

INSERT INTO coach_packages (coach_user_id, name, description, duration_days, price, discount_percentage, is_active, services)
SELECT u.id,
  '6 Aylık Premium',
  'Tam kapsamlı koçluk: antrenman, beslenme, takviye rehberliği, form analizi, haftalık check-in. En popüler paket.',
  180, 7500, 10, TRUE,
  ARRAY['Kişiye Özel Antrenman', 'Beslenme Planı', 'Görüntülü Görüşme', '7/24 Sohbet', 'Haftalık Kontrol', 'İlerleme Takibi', 'Takviye Rehberliği', 'Form Analizi']
FROM users u WHERE u.email = 'elif.demir@fithub.demo'
ON CONFLICT DO NOTHING;

-- Koç 2: Kaan Yıldız (Erkek, Strength & Hypertrophy)
INSERT INTO users (email, password_hash, full_name, role, phone_number, timezone, profile_photo_url, created_at, updated_at)
VALUES (
  'kaan.yildiz@fithub.demo',
  '$2b$12$k.Q0iK5WIW1LzJ.rIM0jaeDh3zmeaG1PwZajLt6kWdezHkg84z4gW',
  'Kaan Yıldız',
  'coach',
  '+905551110002',
  'Europe/Istanbul',
  'https://images.unsplash.com/photo-1567013127542-490d757e51fc?w=400&h=400&fit=crop&crop=face',
  NOW() - INTERVAL '1 year',
  NOW()
) ON CONFLICT (email) DO NOTHING;

INSERT INTO coaches (user_id, bio, photo_url, specialties, title, instagram, twitter, linkedin, website, is_active, rating, rating_count, photos, certificates, referral_code)
SELECT u.id,
  'NSCA-CSCS sertifikalı güç ve kondisyon uzmanı. 10 yılı aşkın deneyimle atletlerden amatörlere kadar geniş bir yelpazede çalışıyorum. Bilimsel temelli programlarla kas gelişimi ve performans artışı sağlıyorum.',
  'https://images.unsplash.com/photo-1567013127542-490d757e51fc?w=800&h=800&fit=crop&crop=face',
  ARRAY['Güç Antrenmanı', 'Kas Geliştirme', 'Atletik Performans', 'HIIT', 'Spor Beslenmesi'],
  'NSCA-CSCS Güç & Kondisyon Uzmanı',
  '@kaanyildiz.coach',
  '@kaan_strength',
  'in/kaanyildiz',
  'https://kaanyildiz.coach',
  TRUE,
  4.8,
  89,
  ARRAY[
    'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=600',
    'https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=600',
    'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=600'
  ],
  ARRAY[
    'https://images.unsplash.com/photo-1576678927484-cc907957088c?w=400'
  ],
  'KAAN30'
FROM users u WHERE u.email = 'kaan.yildiz@fithub.demo'
ON CONFLICT DO NOTHING;

-- Kaan Yıldız paketleri
INSERT INTO coach_packages (coach_user_id, name, description, duration_days, price, discount_percentage, is_active, services)
SELECT u.id,
  '1 Aylık Başlangıç',
  'Antrenman programı + temel beslenme rehberliği. Fitness yolculuğuna ilk adım için ideal.',
  30, 2000, 0, TRUE,
  ARRAY['Kişiye Özel Antrenman', 'Beslenme Planı', '7/24 Sohbet']
FROM users u WHERE u.email = 'kaan.yildiz@fithub.demo'
ON CONFLICT DO NOTHING;

INSERT INTO coach_packages (coach_user_id, name, description, duration_days, price, discount_percentage, is_active, services)
SELECT u.id,
  '3 Aylık Güç Programı',
  'Periodize edilmiş güç programı, makro bazlı beslenme planı, haftalık form video analizi, birebir görüşme.',
  90, 5500, 15, TRUE,
  ARRAY['Kişiye Özel Antrenman', 'Beslenme Planı', 'Görüntülü Görüşme', '7/24 Sohbet', 'Haftalık Kontrol', 'Form Analizi', 'Birebir Antrenman']
FROM users u WHERE u.email = 'kaan.yildiz@fithub.demo'
ON CONFLICT DO NOTHING;

INSERT INTO coach_packages (coach_user_id, name, description, duration_days, price, discount_percentage, is_active, services)
SELECT u.id,
  '12 Aylık Elite',
  'Yıllık tam kapsamlı koçluk. Aylık program güncellemesi, haftalık görüntülü görüşme, takviye protokolü, yarışma hazırlığı.',
  365, 18000, 20, TRUE,
  ARRAY['Kişiye Özel Antrenman', 'Beslenme Planı', 'Görüntülü Görüşme', '7/24 Sohbet', 'Haftalık Kontrol', 'Form Analizi', 'Birebir Antrenman', 'Takviye Rehberliği', 'İlerleme Takibi', 'Mobilite/Esneme']
FROM users u WHERE u.email = 'kaan.yildiz@fithub.demo'
ON CONFLICT DO NOTHING;

-- Koç 3: Selin Aydın (Kadın, Yoga & Mobility)
INSERT INTO users (email, password_hash, full_name, role, phone_number, timezone, profile_photo_url, created_at, updated_at)
VALUES (
  'selin.aydin@fithub.demo',
  '$2b$12$k.Q0iK5WIW1LzJ.rIM0jaeDh3zmeaG1PwZajLt6kWdezHkg84z4gW',
  'Selin Aydın',
  'coach',
  '+905551110003',
  'Europe/Istanbul',
  'https://images.unsplash.com/photo-1518310383802-640c2de311b2?w=400&h=400&fit=crop&crop=face',
  NOW() - INTERVAL '3 months',
  NOW()
) ON CONFLICT (email) DO NOTHING;

INSERT INTO coaches (user_id, bio, photo_url, specialties, title, instagram, twitter, linkedin, website, is_active, rating, rating_count, photos, certificates, referral_code)
SELECT u.id,
  'RYT-500 sertifikalı yoga eğitmeni ve mobilite uzmanı. Stres yönetimi, esneklik ve postür düzeltme konularında 6 yıllık deneyim. Bedenini tanı, sınırlarını aş.',
  'https://images.unsplash.com/photo-1518310383802-640c2de311b2?w=800&h=800&fit=crop&crop=face',
  ARRAY['Yoga', 'Mobilite', 'Esneme', 'Pilates', 'Rehabilitasyon', 'Postür'],
  'RYT-500 Yoga & Mobilite Uzmanı',
  '@selinaydin.yoga',
  NULL,
  'in/selinaydin',
  'https://selinaydin.yoga',
  TRUE,
  5.0,
  43,
  ARRAY[
    'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=600',
    'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=600'
  ],
  ARRAY[
    'https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?w=400'
  ],
  'SELIN20'
FROM users u WHERE u.email = 'selin.aydin@fithub.demo'
ON CONFLICT DO NOTHING;

-- Selin Aydın paketi
INSERT INTO coach_packages (coach_user_id, name, description, duration_days, price, discount_percentage, is_active, services)
SELECT u.id,
  '3 Aylık Denge Programı',
  'Kişiye özel yoga + mobilite programı, haftalık online seans, nefes teknikleri rehberliği, meditasyon desteği.',
  90, 3500, 0, TRUE,
  ARRAY['Kişiye Özel Antrenman', 'Görüntülü Görüşme', '7/24 Sohbet', 'Haftalık Kontrol', 'Mobilite/Esneme']
FROM users u WHERE u.email = 'selin.aydin@fithub.demo'
ON CONFLICT DO NOTHING;


-- ────────────────────────────────────────────
-- 2. MOCK ÖĞRENCİLER (2 adet)
-- ────────────────────────────────────────────

-- Öğrenci 1: Deniz Korkmaz (Erkek, Kaan'ın öğrencisi)
INSERT INTO users (email, password_hash, full_name, role, phone_number, timezone, profile_photo_url, created_at, updated_at)
VALUES (
  'deniz.korkmaz@fithub.demo',
  '$2b$12$k.Q0iK5WIW1LzJ.rIM0jaeDh3zmeaG1PwZajLt6kWdezHkg84z4gW',
  'Deniz Korkmaz',
  'client',
  '+905552220001',
  'Europe/Istanbul',
  'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face',
  NOW() - INTERVAL '2 months',
  NOW()
) ON CONFLICT (email) DO NOTHING;

-- Client row (Kaan'a atanmış)
INSERT INTO clients (user_id, assigned_coach_id, onboarding_done, gender, height_cm, weight_kg, goal_type, created_at, updated_at)
SELECT
  student.id,
  coach.id,
  TRUE,
  'Male',
  182,
  85.5,
  'gain_muscle',
  NOW() - INTERVAL '2 months',
  NOW()
FROM users student, users coach
WHERE student.email = 'deniz.korkmaz@fithub.demo'
  AND coach.email = 'kaan.yildiz@fithub.demo'
ON CONFLICT (user_id) DO UPDATE SET
  assigned_coach_id = EXCLUDED.assigned_coach_id,
  onboarding_done = TRUE,
  gender = 'Male',
  height_cm = 182,
  weight_kg = 85.5,
  goal_type = 'gain_muscle';

-- Onboarding data
INSERT INTO client_onboarding (user_id, full_name, age, weight_kg, height_cm, gender, your_goal, body_type, experience, how_fit, knee_pain, pushups, commit, pref_workout_length, body_part_focus, workout_place, preferred_workout_days, nutrition_budget, target_weight_kg, health_problems, food_allergies, supplements, wakeup_time, sleep_time)
SELECT u.id,
  'Deniz Korkmaz', 27, 85.5, 182, 'Male', 'gain_muscle', 'mesomorph', 'intermediate', 'moderately_fit', 'no', '20_plus', 'least_6_months', 'medium',
  '["Göğüs", "Sırt", "Omuz"]'::jsonb,
  '["gym"]'::jsonb,
  '["mon", "tue", "wed", "thu", "fri"]'::jsonb,
  'medium', 90.0,
  ARRAY[]::text[], ARRAY[]::text[],
  ARRAY['Whey Protein', 'Kreatin', 'BCAA'],
  '07:00', '23:00'
FROM users u WHERE u.email = 'deniz.korkmaz@fithub.demo'
ON CONFLICT (user_id) DO UPDATE SET
  full_name = EXCLUDED.full_name,
  age = EXCLUDED.age, weight_kg = EXCLUDED.weight_kg, height_cm = EXCLUDED.height_cm,
  gender = EXCLUDED.gender, your_goal = EXCLUDED.your_goal, body_type = EXCLUDED.body_type,
  experience = EXCLUDED.experience, how_fit = EXCLUDED.how_fit, knee_pain = EXCLUDED.knee_pain,
  pushups = EXCLUDED.pushups, commit = EXCLUDED.commit, pref_workout_length = EXCLUDED.pref_workout_length,
  body_part_focus = EXCLUDED.body_part_focus, workout_place = EXCLUDED.workout_place,
  preferred_workout_days = EXCLUDED.preferred_workout_days,
  nutrition_budget = EXCLUDED.nutrition_budget, target_weight_kg = EXCLUDED.target_weight_kg,
  health_problems = EXCLUDED.health_problems, food_allergies = EXCLUDED.food_allergies,
  supplements = EXCLUDED.supplements, wakeup_time = EXCLUDED.wakeup_time, sleep_time = EXCLUDED.sleep_time;

-- Subscription (Kaan'ın 3 Aylık Güç Programı)
INSERT INTO subscriptions (client_user_id, coach_user_id, plan_name, status, started_at, ends_at, program_state, program_assigned_at, created_at)
SELECT student.id, coach.id,
  '3 Aylık Güç Programı', 'active',
  NOW() - INTERVAL '45 days',
  NOW() + INTERVAL '45 days',
  'assigned', NOW() - INTERVAL '44 days',
  NOW() - INTERVAL '45 days'
FROM users student, users coach
WHERE student.email = 'deniz.korkmaz@fithub.demo'
  AND coach.email = 'kaan.yildiz@fithub.demo'
ON CONFLICT DO NOTHING;

-- Weight progress (son 8 hafta — azalan trend, kas ağırlığı artış)
INSERT INTO body_measurements (user_id, measured_at, weight_kg, chest_cm, waist_cm, left_arm_cm, right_arm_cm, notes)
SELECT u.id, d::date, w, c, wa, la, ra, n
FROM users u,
(VALUES
  (NOW() - INTERVAL '56 days', 85.5, 100.0, 84.0, 36.0, 36.5, 'Başlangıç ölçümleri'),
  (NOW() - INTERVAL '49 days', 85.0, 100.5, 83.5, 36.2, 36.7, NULL),
  (NOW() - INTERVAL '42 days', 84.3, 101.0, 83.0, 36.5, 37.0, NULL),
  (NOW() - INTERVAL '35 days', 84.0, 101.5, 82.5, 37.0, 37.2, '4. hafta — iyi ilerleme'),
  (NOW() - INTERVAL '28 days', 83.5, 102.0, 82.0, 37.2, 37.5, NULL),
  (NOW() - INTERVAL '21 days', 83.8, 102.0, 81.5, 37.5, 37.8, NULL),
  (NOW() - INTERVAL '14 days', 83.2, 102.5, 81.0, 37.8, 38.0, '6. hafta — bel incelmesi belirgin'),
  (NOW() - INTERVAL '7 days',  82.8, 103.0, 80.5, 38.0, 38.2, NULL)
) AS v(d, w, c, wa, la, ra, n)
WHERE u.email = 'deniz.korkmaz@fithub.demo'
ON CONFLICT DO NOTHING;

-- Badges earned
INSERT INTO user_badges (user_id, badge_id, earned_at)
SELECT u.id, b, NOW() - INTERVAL '45 days'
FROM users u,
(VALUES ('first_login'), ('onboarding_complete'), ('first_coach'), ('first_workout'), ('first_message'), ('first_weighin'), ('first_measurement'), ('member_7'), ('member_30')) AS v(b)
WHERE u.email = 'deniz.korkmaz@fithub.demo'
ON CONFLICT DO NOTHING;


-- Öğrenci 2: Buse Çelik (Kadın, Elif'in öğrencisi)
INSERT INTO users (email, password_hash, full_name, role, phone_number, timezone, profile_photo_url, created_at, updated_at)
VALUES (
  'buse.celik@fithub.demo',
  '$2b$12$k.Q0iK5WIW1LzJ.rIM0jaeDh3zmeaG1PwZajLt6kWdezHkg84z4gW',
  'Buse Çelik',
  'client',
  '+905552220002',
  'Europe/Istanbul',
  'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=400&fit=crop&crop=face',
  NOW() - INTERVAL '3 months',
  NOW()
) ON CONFLICT (email) DO NOTHING;

-- Client row (Elif'e atanmış)
INSERT INTO clients (user_id, assigned_coach_id, onboarding_done, gender, height_cm, weight_kg, goal_type, created_at, updated_at)
SELECT
  student.id,
  coach.id,
  TRUE,
  'Female',
  165,
  68.0,
  'lose_weight',
  NOW() - INTERVAL '3 months',
  NOW()
FROM users student, users coach
WHERE student.email = 'buse.celik@fithub.demo'
  AND coach.email = 'elif.demir@fithub.demo'
ON CONFLICT (user_id) DO UPDATE SET
  assigned_coach_id = EXCLUDED.assigned_coach_id,
  onboarding_done = TRUE,
  gender = 'Female',
  height_cm = 165,
  weight_kg = 68.0,
  goal_type = 'lose_weight';

-- Onboarding data
INSERT INTO client_onboarding (user_id, full_name, age, weight_kg, height_cm, gender, your_goal, body_type, experience, how_fit, knee_pain, pushups, commit, pref_workout_length, body_part_focus, workout_place, preferred_workout_days, nutrition_budget, target_weight_kg, health_problems, food_allergies, supplements, wakeup_time, sleep_time)
SELECT u.id,
  'Buse Çelik', 24, 68.0, 165, 'Female', 'lose_weight', 'endomorph', 'beginner', 'not_fit', 'no', 'zero_to_5', 'least_3_months', 'short',
  '["Bacak", "Kalça", "Karın"]'::jsonb,
  '["gym", "home"]'::jsonb,
  '["mon", "wed", "fri", "sat"]'::jsonb,
  'low', 58.0,
  ARRAY[]::text[],
  ARRAY['Laktoz']::text[],
  ARRAY['Multivitamin']::text[],
  '06:30', '22:30'
FROM users u WHERE u.email = 'buse.celik@fithub.demo'
ON CONFLICT (user_id) DO UPDATE SET
  full_name = EXCLUDED.full_name,
  age = EXCLUDED.age, weight_kg = EXCLUDED.weight_kg, height_cm = EXCLUDED.height_cm,
  gender = EXCLUDED.gender, your_goal = EXCLUDED.your_goal, body_type = EXCLUDED.body_type,
  experience = EXCLUDED.experience, how_fit = EXCLUDED.how_fit, knee_pain = EXCLUDED.knee_pain,
  pushups = EXCLUDED.pushups, commit = EXCLUDED.commit, pref_workout_length = EXCLUDED.pref_workout_length,
  body_part_focus = EXCLUDED.body_part_focus, workout_place = EXCLUDED.workout_place,
  preferred_workout_days = EXCLUDED.preferred_workout_days,
  nutrition_budget = EXCLUDED.nutrition_budget, target_weight_kg = EXCLUDED.target_weight_kg,
  health_problems = EXCLUDED.health_problems, food_allergies = EXCLUDED.food_allergies,
  supplements = EXCLUDED.supplements, wakeup_time = EXCLUDED.wakeup_time, sleep_time = EXCLUDED.sleep_time;

-- Subscription (Elif'in 6 Aylık Premium)
INSERT INTO subscriptions (client_user_id, coach_user_id, plan_name, status, started_at, ends_at, program_state, program_assigned_at, created_at)
SELECT student.id, coach.id,
  '6 Aylık Premium', 'active',
  NOW() - INTERVAL '75 days',
  NOW() + INTERVAL '105 days',
  'assigned', NOW() - INTERVAL '74 days',
  NOW() - INTERVAL '75 days'
FROM users student, users coach
WHERE student.email = 'buse.celik@fithub.demo'
  AND coach.email = 'elif.demir@fithub.demo'
ON CONFLICT DO NOTHING;

-- Weight progress (kilo verme trend)
INSERT INTO body_measurements (user_id, measured_at, weight_kg, waist_cm, hips_cm, notes)
SELECT u.id, d::date, w, wa, h, n
FROM users u,
(VALUES
  (NOW() - INTERVAL '75 days', 68.0, 78.0, 102.0, 'Başlangıç'),
  (NOW() - INTERVAL '65 days', 67.2, 77.5, 101.5, NULL),
  (NOW() - INTERVAL '55 days', 66.5, 76.8, 101.0, NULL),
  (NOW() - INTERVAL '45 days', 65.8, 76.0, 100.0, 'İlk ay — harika ilerleme!'),
  (NOW() - INTERVAL '35 days', 65.0, 75.2, 99.5, NULL),
  (NOW() - INTERVAL '25 days', 64.5, 74.5, 98.5, NULL),
  (NOW() - INTERVAL '15 days', 63.8, 73.8, 98.0, '2. ay — hedefte'),
  (NOW() - INTERVAL '5 days',  63.2, 73.0, 97.0, NULL)
) AS v(d, w, wa, h, n)
WHERE u.email = 'buse.celik@fithub.demo'
ON CONFLICT DO NOTHING;

-- Badges earned (daha fazla — aktif öğrenci)
INSERT INTO user_badges (user_id, badge_id, earned_at)
SELECT u.id, b, NOW() - INTERVAL '60 days'
FROM users u,
(VALUES ('first_login'), ('onboarding_complete'), ('first_coach'), ('first_workout'), ('first_message'), ('first_weighin'), ('first_measurement'), ('first_meal_photo'), ('all_meals_logged'), ('transformation'), ('member_7'), ('member_30'), ('member_90'), ('streak_7')) AS v(b)
WHERE u.email = 'buse.celik@fithub.demo'
ON CONFLICT DO NOTHING;


-- ────────────────────────────────────────────
-- 3. DOĞRULAMA
-- ────────────────────────────────────────────

SELECT '=== Demo Koçlar ===' AS section;
SELECT u.id, u.full_name, u.email, c.rating, array_length(c.specialties, 1) AS specialty_count
FROM users u JOIN coaches c ON c.user_id = u.id
WHERE u.email LIKE '%@fithub.demo'
ORDER BY u.full_name;

SELECT '=== Demo Öğrenciler ===' AS section;
SELECT u.id, u.full_name, u.email, cl.assigned_coach_id, cl.weight_kg, cl.goal_type
FROM users u JOIN clients cl ON cl.user_id = u.id
WHERE u.email LIKE '%@fithub.demo'
ORDER BY u.full_name;

SELECT '=== Demo Paketler ===' AS section;
SELECT cp.name, cp.price, cp.duration_days, u.full_name AS coach
FROM coach_packages cp JOIN users u ON u.id = cp.coach_user_id
WHERE u.email LIKE '%@fithub.demo'
ORDER BY u.full_name, cp.price;

SELECT '=== Demo Ölçümler ===' AS section;
SELECT u.full_name, COUNT(*) AS measurement_count
FROM body_measurements bm JOIN users u ON u.id = bm.user_id
WHERE u.email LIKE '%@fithub.demo'
GROUP BY u.full_name;

SELECT '=== Demo Rozetler ===' AS section;
SELECT u.full_name, COUNT(*) AS badge_count
FROM user_badges ub JOIN users u ON u.id = ub.user_id
WHERE u.email LIKE '%@fithub.demo'
GROUP BY u.full_name;
