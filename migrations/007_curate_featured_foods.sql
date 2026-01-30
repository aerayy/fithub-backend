-- Curation: Mark featured foods and set piece_weight_g for Adet support
-- Run after 006_food_featured_and_piece_weight.sql

-- 1) piece_weight_g: 1 adet = ortalama gram (Adet seçeneği için)
UPDATE food_localization_tr SET piece_weight_g = 50
WHERE name_tr ILIKE '%yumurta%';

UPDATE food_localization_tr SET piece_weight_g = 120
WHERE name_tr ILIKE '%muz%' AND name_tr ILIKE '%çiğ%';

UPDATE food_localization_tr SET piece_weight_g = 180
WHERE name_tr ILIKE '%elma%';

UPDATE food_localization_tr SET piece_weight_g = 130
WHERE name_tr ILIKE '%portakal%';

-- 2) is_featured: Sadece yaygın, tekil besinler (duplicate/gereksizleri hariç)
-- Tavuk - sadece göğüs ve but (derisiz)
UPDATE food_localization_tr SET is_featured = TRUE
WHERE name_tr IN ('Derisiz Tavuk But', 'Tavuk Göğsü', 'Çiğ Tavuk Gogsu')
   OR (name_tr ILIKE '%tavuk%göğ%' OR name_tr ILIKE '%chicken%breast%')
   OR (name_tr ILIKE '%tavuk%but%' AND name_tr ILIKE '%derisiz%');

-- Yumurta
UPDATE food_localization_tr SET is_featured = TRUE
WHERE name_tr ILIKE '%yumurta%' AND (name_tr ILIKE '%büyük%' OR name_tr ILIKE '%whole%' OR name_tr ILIKE '%beyaz%' OR name_tr ILIKE '%sarısı%');

-- Pirinç, yulaf, makarna
UPDATE food_localization_tr SET is_featured = TRUE
WHERE name_tr ILIKE '%pirinç%' OR name_tr ILIKE '%rice%'
   OR name_tr ILIKE '%yulaf%' OR name_tr ILIKE '%oat%'
   OR name_tr ILIKE '%makarna%' OR name_tr ILIKE '%pasta%'
   OR name_tr ILIKE '%bulgur%' OR name_tr ILIKE '%quinoa%';

-- Et, balık
UPDATE food_localization_tr SET is_featured = TRUE
WHERE name_tr ILIKE '%somon%' OR name_tr ILIKE '%salmon%'
   OR name_tr ILIKE '%ton%' OR name_tr ILIKE '%tuna%'
   OR name_tr ILIKE '%bonfile%' OR name_tr ILIKE '%dana%'
   OR name_tr ILIKE '%hindi%' OR name_tr ILIKE '%turkey%';

-- Sebzeler
UPDATE food_localization_tr SET is_featured = TRUE
WHERE name_tr ILIKE '%brokoli%' OR name_tr ILIKE '%ıspanak%'
   OR name_tr ILIKE '%domates%' OR name_tr ILIKE '%salatalık%'
   OR name_tr ILIKE '%havuç%' OR name_tr ILIKE '%marul%'
   OR name_tr ILIKE '%biber%' OR name_tr ILIKE '%fasulye%';

-- Meyveler
UPDATE food_localization_tr SET is_featured = TRUE
WHERE name_tr ILIKE '%muz%' OR name_tr ILIKE '%elma%'
   OR name_tr ILIKE '%portakal%' OR name_tr ILIKE '%avokado%'
   OR name_tr ILIKE '%çilek%' OR name_tr ILIKE '%yaban mersin%';

-- Süt ürünleri
UPDATE food_localization_tr SET is_featured = TRUE
WHERE name_tr ILIKE '%yoğurt%' OR name_tr ILIKE '%yogurt%'
   OR name_tr ILIKE '%süt%' OR name_tr ILIKE '%milk%'
   OR name_tr ILIKE '%peynir%' OR name_tr ILIKE '%cheese%'
   OR name_tr ILIKE '%lor%' OR name_tr ILIKE '%cottage%';

-- Ekmek, tahıl
UPDATE food_localization_tr SET is_featured = TRUE
WHERE name_tr ILIKE '%ekmek%' AND name_tr NOT ILIKE '%strudel%' AND name_tr NOT ILIKE '%croissant%';

-- Patates, tatlı patates
UPDATE food_localization_tr SET is_featured = TRUE
WHERE name_tr ILIKE '%patates%' OR name_tr ILIKE '%potato%';

-- Yağlar
UPDATE food_localization_tr SET is_featured = TRUE
WHERE name_tr ILIKE '%zeytinyağ%' OR name_tr ILIKE '%olive oil%'
   OR name_tr ILIKE '%avokado%' OR name_tr ILIKE '%hindistan cevizi yağ%';
