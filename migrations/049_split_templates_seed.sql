-- Migration 049: split_templates seed — initial 6 family.
--
-- Mimari karar (project_workout_generator_v3.md):
--   Beginner default = FB/UL only (PPL'i locklamak için experience_lock).
--   Intermediate = PPL'e geçiş açık.
--   Advanced = Arnold/hybrid serbest.
--
-- Day-session yapısı: muscles array'i SplitPlanner'a "hangi kas gruplarını
-- hangi gün çalıştır" sinyalini verir; VolumePlanner buna göre per-session
-- set hedefi hesaplar.
--
-- Daha sonra yeni split eklemek = sadece INSERT row. Kod değişikliği yok.

BEGIN;

-- ── Full Body (beginner uyumlu) ───────────────────────────────────────
INSERT INTO split_templates
  (split_id, display_name, family, days_per_week, experience_lock, goal_match, day_sessions, rank, rationale)
VALUES (
  'fb3',
  'Tüm Vücut × 3',
  'fb',
  3,
  ARRAY['beginner','intermediate']::TEXT[],   -- ileri lvl için fb_3 yetersiz
  ARRAY['hypertrophy','general','strength','fat_loss']::TEXT[],
  '[
    {"name":"Tüm Vücut A","muscles":["chest","back","quads","shoulder","biceps"]},
    {"name":"Tüm Vücut B","muscles":["back","glutes","hamstrings","chest","triceps","core"]},
    {"name":"Tüm Vücut C","muscles":["quads","shoulder","back","biceps","triceps","core"]}
  ]'::JSONB,
  10,
  'Beginner için ideal: her kas grubu haftada 2-3× frekans, recovery yeterli, motor learning hızlı.'
);

INSERT INTO split_templates
  (split_id, display_name, family, days_per_week, experience_lock, goal_match, day_sessions, rank, rationale)
VALUES (
  'fb2',
  'Tüm Vücut × 2',
  'fb',
  2,
  '{}'::TEXT[],
  ARRAY['general','fat_loss','hypertrophy']::TEXT[],
  '[
    {"name":"Tüm Vücut A","muscles":["chest","back","quads","shoulder","biceps","core"]},
    {"name":"Tüm Vücut B","muscles":["back","glutes","hamstrings","chest","triceps","core"]}
  ]'::JSONB,
  20,
  'Minimal frekans — adherence düşük veya çok meşgul kullanıcılar için.'
);

-- ── Upper / Lower (beginner+intermediate) ──────────────────────────────
INSERT INTO split_templates
  (split_id, display_name, family, days_per_week, experience_lock, goal_match, day_sessions, rank, rationale)
VALUES (
  'ul4',
  'Upper / Lower × 4',
  'ul',
  4,
  ARRAY['beginner','intermediate']::TEXT[],
  ARRAY['hypertrophy','strength','general']::TEXT[],
  '[
    {"name":"Upper A","muscles":["chest","back","shoulder","biceps","triceps"]},
    {"name":"Lower A","muscles":["quads","hamstrings","glutes","calves","core"]},
    {"name":"Upper B","muscles":["back","chest","shoulder","triceps","biceps"]},
    {"name":"Lower B","muscles":["glutes","hamstrings","quads","calves","core"]}
  ]'::JSONB,
  10,
  '4 gün için altın standart. Her kas grubu 2× frekans, recovery 48-72h, beginner→intermediate geçişi için ideal.'
);

INSERT INTO split_templates
  (split_id, display_name, family, days_per_week, experience_lock, goal_match, day_sessions, rank, rationale)
VALUES (
  'fb4',
  'Tüm Vücut × 4',
  'fb',
  4,
  ARRAY['beginner']::TEXT[],
  ARRAY['general','strength','hypertrophy']::TEXT[],
  '[
    {"name":"Tüm Vücut A","muscles":["chest","back","quads","shoulder"]},
    {"name":"Tüm Vücut B","muscles":["back","hamstrings","glutes","triceps","core"]},
    {"name":"Tüm Vücut C","muscles":["chest","shoulder","quads","biceps","core"]},
    {"name":"Tüm Vücut D","muscles":["back","glutes","hamstrings","triceps","core"]}
  ]'::JSONB,
  20,
  'Beginner için 4 gün full body alternatifi — UL''den daha yüksek frekans, fakat seans başı daha az hacim.'
);

-- ── PPL (intermediate+, beginner kilitli) ──────────────────────────────
INSERT INTO split_templates
  (split_id, display_name, family, days_per_week, experience_lock, goal_match, day_sessions, rank, rationale)
VALUES (
  'ppl5',
  'Push / Pull / Legs / Upper / Lower',
  'ppl',
  5,
  ARRAY['intermediate','advanced']::TEXT[],
  ARRAY['hypertrophy','strength']::TEXT[],
  '[
    {"name":"Push","muscles":["chest","shoulder","triceps"]},
    {"name":"Pull","muscles":["back","biceps","rear_delts"]},
    {"name":"Legs","muscles":["quads","hamstrings","glutes","calves","core"]},
    {"name":"Upper","muscles":["chest","back","shoulder","biceps","triceps"]},
    {"name":"Lower","muscles":["glutes","hamstrings","quads","calves","core"]}
  ]'::JSONB,
  10,
  '5 gün PPL + UL. Her kas grubu 2× frekans (PPL tek başına 1×, UL ile 2× olur).'
);

INSERT INTO split_templates
  (split_id, display_name, family, days_per_week, experience_lock, goal_match, day_sessions, rank, rationale)
VALUES (
  'ppl3',
  'Push / Pull / Legs × 1',
  'ppl',
  3,
  ARRAY['intermediate','advanced']::TEXT[],
  ARRAY['hypertrophy','strength']::TEXT[],
  '[
    {"name":"Push","muscles":["chest","shoulder","triceps"]},
    {"name":"Pull","muscles":["back","biceps","rear_delts"]},
    {"name":"Legs","muscles":["quads","hamstrings","glutes","calves","core"]}
  ]'::JSONB,
  30,
  '3 gün PPL — düşük frekans (1× weekly per muscle), kısa programlar için.'
);

INSERT INTO split_templates
  (split_id, display_name, family, days_per_week, experience_lock, goal_match, day_sessions, rank, rationale)
VALUES (
  'ppl6',
  'PPL × 2',
  'ppl',
  6,
  ARRAY['intermediate','advanced']::TEXT[],
  ARRAY['hypertrophy','strength']::TEXT[],
  '[
    {"name":"Push A","muscles":["chest","shoulder","triceps"]},
    {"name":"Pull A","muscles":["back","biceps","rear_delts"]},
    {"name":"Legs A","muscles":["quads","hamstrings","glutes","calves","core"]},
    {"name":"Push B","muscles":["chest","shoulder","triceps"]},
    {"name":"Pull B","muscles":["back","biceps","rear_delts"]},
    {"name":"Legs B","muscles":["glutes","hamstrings","quads","calves","core"]}
  ]'::JSONB,
  10,
  'Yüksek hacim/frekans. Her kas 2× weekly, advanced için MAV''e yaklaşır.'
);

-- ── Arnold split (advanced) ────────────────────────────────────────────
INSERT INTO split_templates
  (split_id, display_name, family, days_per_week, experience_lock, goal_match, day_sessions, rank, rationale)
VALUES (
  'arnold6',
  'Arnold Split (Chest/Back + Shoulders/Arms + Legs) × 2',
  'arnold',
  6,
  ARRAY['advanced']::TEXT[],
  ARRAY['hypertrophy','aesthetic']::TEXT[],
  '[
    {"name":"Chest + Back A","muscles":["chest","back"]},
    {"name":"Shoulders + Arms A","muscles":["shoulder","biceps","triceps","rear_delts"]},
    {"name":"Legs A","muscles":["quads","hamstrings","glutes","calves","core"]},
    {"name":"Chest + Back B","muscles":["chest","back"]},
    {"name":"Shoulders + Arms B","muscles":["shoulder","biceps","triceps","rear_delts"]},
    {"name":"Legs B","muscles":["glutes","hamstrings","quads","calves","core"]}
  ]'::JSONB,
  20,
  'Klasik bodybuilding split — yüksek hacim, gelişmiş recovery gerektirir.'
);

-- ── Hybrid / specialization examples (future extensibility kanıtı) ─────
-- Yeni split eklemek için bu pattern'ı takip et. Kod değişmiyor.
INSERT INTO split_templates
  (split_id, display_name, family, days_per_week, experience_lock, goal_match, day_sessions, rank, rationale, active)
VALUES (
  'glute_focus_5',
  'Alt Vücut Vurgulu × 5 (Glute Specialization)',
  'specialization',
  5,
  ARRAY['intermediate','advanced']::TEXT[],
  ARRAY['hypertrophy','aesthetic']::TEXT[],
  '[
    {"name":"Lower A (Glute Priority)","muscles":["glutes","hamstrings","quads","calves"]},
    {"name":"Upper","muscles":["back","chest","shoulder","biceps","triceps"]},
    {"name":"Lower B (Quad Priority)","muscles":["quads","glutes","hamstrings","calves"]},
    {"name":"Upper (Push)","muscles":["chest","shoulder","triceps","core"]},
    {"name":"Lower C (Hip Hinge)","muscles":["glutes","hamstrings","core"]}
  ]'::JSONB,
  40,
  'Alt vücut frekansı 3×, üst vücut 2×. Glute hypertrophy önceliği — kullanıcı kendisi seçtiğinde kullanılır.',
  TRUE
);

COMMIT;
