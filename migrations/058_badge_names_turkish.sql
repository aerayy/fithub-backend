-- 058: Rozet ad/açıklamaları ASCII yazılmıştı ("Ilk Adim", "Koc Buldum") —
-- profilde bozuk Türkçe görünüyordu. Doğru karakterlerle güncellenir.
-- (badge_definitions.id = rozet anahtarı)
BEGIN;
UPDATE badge_definitions SET name_tr = 'İlk Adım',            description_tr = 'Uygulamaya ilk kez giriş yaptın'              WHERE id = 'first_login';
UPDATE badge_definitions SET name_tr = 'Profil Tamam',        description_tr = 'Profil kurulumunu tamamladın'                 WHERE id = 'onboarding_complete';
UPDATE badge_definitions SET name_tr = 'Koç Buldum',          description_tr = 'İlk kez bir koç seçtin'                       WHERE id = 'first_coach';
UPDATE badge_definitions SET name_tr = 'Fit AI Koç',          description_tr = 'Fit AI Koç paketini aktif ettin'              WHERE id = 'ai_coach';
UPDATE badge_definitions SET name_tr = 'İlk Antrenman',       description_tr = 'İlk antrenmanını tamamladın'                  WHERE id = 'first_workout';
UPDATE badge_definitions SET name_tr = '3 Gün Serisi',        description_tr = '3 gün üst üste antrenman yaptın'              WHERE id = 'streak_3';
UPDATE badge_definitions SET name_tr = 'Haftalık Savaş',      description_tr = '7 gün üst üste antrenman yaptın'              WHERE id = 'streak_7';
UPDATE badge_definitions SET name_tr = 'Demir İrade',         description_tr = '30 gün üst üste antrenman yaptın'             WHERE id = 'streak_30';
UPDATE badge_definitions SET name_tr = 'İlk Öğün Fotoğrafı',  description_tr = 'İlk öğün fotoğrafını gönderdin'               WHERE id = 'first_meal_photo';
UPDATE badge_definitions SET name_tr = 'Tam Gün Takip',       description_tr = 'Bir günde tüm öğünleri kaydettin'             WHERE id = 'all_meals_logged';
UPDATE badge_definitions SET name_tr = 'İlk Tartılma',        description_tr = 'İlk kilo kaydını girdin'                      WHERE id = 'first_weighin';
UPDATE badge_definitions SET name_tr = 'Ölçü Alındı',         description_tr = 'İlk vücut ölçünü girdin'                      WHERE id = 'first_measurement';
UPDATE badge_definitions SET name_tr = '1 Haftalık Üye',      description_tr = '7 gündür üyesin'                              WHERE id = 'member_7';
UPDATE badge_definitions SET name_tr = '1 Aylık Üye',         description_tr = '30 gündür üyesin'                             WHERE id = 'member_30';
UPDATE badge_definitions SET name_tr = '3 Aylık Üye',         description_tr = '90 gündür üyesin'                             WHERE id = 'member_90';
UPDATE badge_definitions SET name_tr = 'İlk Mesaj',           description_tr = 'Koçuna ilk mesajını gönderdin'                WHERE id = 'first_message';
UPDATE badge_definitions SET name_tr = 'Değerlendirme',       description_tr = 'İlk 2 haftalık değerlendirmeni tamamladın'   WHERE id = 'checkin_complete';
UPDATE badge_definitions SET name_tr = 'Dönüşüm Başlıyor',    description_tr = 'İlk ilerleme fotoğrafını yükledin'            WHERE id = 'transformation';
-- AI koç sanal kullanıcısının görünen adı
UPDATE users SET full_name = 'Fit AI Koç' WHERE id = 60;
COMMIT;
