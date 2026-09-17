-- 067: Uygulama genel ayarları / özellik bayrakları (sunucudan yönetilir, uygulama güncellemesi gerektirmez).
-- features.real_coaches_enabled = false → istemci uygulaması gerçek koç keşif/satın alma akışlarını gizler,
-- "yakında" kartı gösterir; koçu zaten atanmış öğrencilerin mevcut akışı etkilenmez.
CREATE TABLE IF NOT EXISTS app_settings (
    key        TEXT PRIMARY KEY,
    value      JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO app_settings (key, value)
VALUES ('features', '{"real_coaches_enabled": false, "ai_coach_trial_days": 7, "ai_coach_name": "FitHub AI Coach"}'::jsonb)
ON CONFLICT (key) DO NOTHING;
