-- Badges: definitions catalog + user-earned tracking
-- Idempotent: safe to run on existing DB (CREATE TABLE IF NOT EXISTS, ON CONFLICT DO NOTHING)

-- Badge catalog (static definitions)
CREATE TABLE IF NOT EXISTS badge_definitions (
    id              VARCHAR(50) PRIMARY KEY,         -- e.g. 'first_workout'
    name_tr         VARCHAR(100) NOT NULL,           -- e.g. 'İlk Antrenman'
    description_tr  TEXT NOT NULL,                   -- earn condition copy
    icon            VARCHAR(50) NOT NULL,            -- maps to Flutter _iconMap key
    category        VARCHAR(30) NOT NULL,            -- onboarding/coaching/workout/nutrition/progress/milestone/social/general
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- User-earned badges (one row per user×badge)
CREATE TABLE IF NOT EXISTS user_badges (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id    VARCHAR(50) NOT NULL REFERENCES badge_definitions(id) ON DELETE CASCADE,
    earned_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, badge_id)
);

CREATE INDEX IF NOT EXISTS idx_user_badges_user
    ON user_badges(user_id, earned_at DESC);

CREATE INDEX IF NOT EXISTS idx_badge_definitions_sort
    ON badge_definitions(sort_order);

-- Seed: 18 starter badges
-- Categories (must match Flutter _categoryColors):
--   onboarding, coaching, workout, nutrition, progress, milestone, social, general
INSERT INTO badge_definitions (id, name_tr, description_tr, icon, category, sort_order) VALUES
    ('first_login',          'İlk Adım',           'Uygulamaya ilk girişin için.',                                       'login',                  'onboarding', 10),
    ('onboarding_complete',  'Profil Tamam',       'Onboarding adımlarını tamamladın.',                                  'person_check',           'onboarding', 20),
    ('first_coach',          'Koç Buldum',         'İlk koçunla anlaştın.',                                              'sports',                 'coaching',   30),
    ('ai_coach',             'AI Koç',             'AI Koç ile yolculuğa başladın.',                                     'psychology',             'coaching',   40),
    ('first_workout',        'İlk Antrenman',      'İlk antrenmanını tamamladın.',                                       'fitness_center',         'workout',    50),
    ('streak_7',             '7 Günlük Seri',      'Üst üste 7 gün antrenman yaptın.',                                   'local_fire_department',  'workout',    60),
    ('streak_30',            '30 Günlük Seri',     'Üst üste 30 gün antrenman yaptın.',                                  'whatshot',               'workout',    70),
    ('streak_100',           '100 Günlük Seri',    'Üst üste 100 gün antrenman yaptın.',                                 'military_tech',          'workout',    80),
    ('first_meal_photo',     'İlk Öğün Fotoğrafı', 'İlk öğün fotoğrafını paylaştın.',                                    'camera_alt',             'nutrition',  90),
    ('all_meals_logged',     'Tam Beslenme Günü',  'Bir günde tüm öğünlerini eksiksiz logladın.',                        'restaurant',             'nutrition', 100),
    ('first_weighin',        'İlk Tartı',          'İlk kez kilonu kaydettin.',                                          'monitor_weight',         'progress', 110),
    ('first_measurement',    'İlk Ölçüm',          'İlk vücut ölçümlerini kaydettin.',                                   'straighten',             'progress', 120),
    ('transformation',       'Dönüşüm',            'İlk vücut form fotoğrafını yükledin.',                               'compare',                'progress', 130),
    ('member_7',             '1 Haftalık Üye',     '7 gündür FitHub ailesindesin.',                                      'card_membership',        'milestone', 140),
    ('member_30',            '1 Aylık Üye',        '30 gündür FitHub ailesindesin.',                                     'workspace_premium',      'milestone', 150),
    ('member_90',            '3 Aylık Üye',        '90 gündür FitHub ailesindesin.',                                     'diamond',                'milestone', 160),
    ('first_message',        'İlk Mesaj',          'Koçuna ilk mesajını gönderdin.',                                     'chat',                   'social',   170),
    ('checkin_complete',     'İlk Check-in',       'İlk haftalık check-in formunu tamamladın.',                          'assignment_turned_in',   'general',  180)
ON CONFLICT (id) DO NOTHING;
