-- 060: sık sorgulanan tablolarda eksik indeksler.
-- Idempotent: tablo/kolon varsa ve indeks yoksa oluşturur (lokal/prod şema farkı deploy'u kırmaz).
DO $$
DECLARE
  spec RECORD;
BEGIN
  FOR spec IN
    SELECT * FROM (VALUES
      ('workout_exercises',   'workout_day_id', 'idx_workout_exercises_day',        'workout_day_id'),
      ('body_form_analyses',  'client_user_id', 'idx_body_form_analyses_client',    'client_user_id, created_at DESC'),
      ('user_badges',         'user_id',        'idx_user_badges_user',             'user_id'),
      ('daily_water_log',     'user_id',        'idx_daily_water_log_user_date',    'user_id, log_date'),
      ('ai_quota_usage',      'user_id',        'idx_ai_quota_usage_user_month',    'user_id, month_key'),
      ('ai_subscriptions',    'user_id',        'idx_ai_subscriptions_user',        'user_id'),
      ('fcm_tokens',          'fcm_token',      'idx_fcm_tokens_token',             'fcm_token'),
      ('messages',            'sender_user_id', 'idx_messages_sender',              'sender_user_id'),
      ('activity_log',        'client_user_id', 'idx_activity_log_client_created',  'client_user_id, created_at DESC'),
      ('meal_photos',         'client_user_id', 'idx_meal_photos_client_created',   'client_user_id, created_at DESC'),
      ('subscriptions',       'coach_user_id',  'idx_subscriptions_coach_status',   'coach_user_id, status')
    ) AS t(tbl, col, idx, cols)
  LOOP
    IF to_regclass('public.' || spec.tbl) IS NOT NULL
       AND EXISTS (
         SELECT 1 FROM information_schema.columns
         WHERE table_schema = 'public' AND table_name = spec.tbl AND column_name = spec.col
       )
       AND NOT EXISTS (
         SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = spec.idx
       )
    THEN
      EXECUTE format('CREATE INDEX %I ON %I (%s)', spec.idx, spec.tbl, spec.cols);
    END IF;
  END LOOP;
END $$;
