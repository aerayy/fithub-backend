-- Migration: Add is_featured and piece_weight_g for food curation and "Adet" unit
-- is_featured: Sadece öne çıkarılan besinler search'te gösterilsin (opsiyonel filtre)
-- piece_weight_g: 1 adet için ortalama gram (örn: yumurta 50g) - null = sadece gram

ALTER TABLE food_localization_tr
ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;

ALTER TABLE food_localization_tr
ADD COLUMN IF NOT EXISTS piece_weight_g DECIMAL(10, 2);

COMMENT ON COLUMN food_localization_tr.is_featured IS 'Featured foods shown first in coach search (fewer, curated list)';
COMMENT ON COLUMN food_localization_tr.piece_weight_g IS 'Average weight of 1 piece in grams - enables Adet unit in UI';
