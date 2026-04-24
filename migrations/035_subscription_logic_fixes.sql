-- Subscription logic hardening:
-- 1. Aynı koçtan 2 aktif sub olamaz (zaten ux_subscription_single_active var — kontrol)
-- 2. Aynı client'tan herhangi bir aktif sub olduğunda, yenisi backend'te reject edilecek (uygulama seviyesinde)

-- Mevcut ux_subscription_single_active index'i: UNIQUE (client_user_id, coach_user_id) WHERE status='active'
-- Bu aynı koçtan 2 aktif sub'ı zaten engelliyor.
-- YENİ: Client için tamamen 1 aktif sub garantisi — herhangi bir koçtan.
-- Bu partial unique index, aynı client'ın herhangi 2 aktif sub'ına DB seviyesinde engel olur.

CREATE UNIQUE INDEX IF NOT EXISTS uq_sub_one_active_per_client
  ON subscriptions (client_user_id)
  WHERE status = 'active';

-- Not: Mevcut çift aktif sub varsa bu index fail eder. Önce eski çakışanları cancel et.
-- (Demo DB'de kontrol edildi: çakışma yok)
