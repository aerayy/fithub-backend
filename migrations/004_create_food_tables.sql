-- Migration: Create food tables for USDA-based food database
-- Purpose: Store food items, macros, and Turkish localization

-- Food items (from USDA FoodData Central)
CREATE TABLE IF NOT EXISTS food_items (
    id SERIAL PRIMARY KEY,
    fdc_id INTEGER UNIQUE,  -- USDA FoodData Central ID (nullable for custom foods)
    name_en VARCHAR(500) NOT NULL,
    description TEXT,
    data_type VARCHAR(50),  -- "Foundation", "SR Legacy", "Survey", "Branded"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_food_items_name_en ON food_items(name_en);
CREATE INDEX idx_food_items_fdc_id ON food_items(fdc_id) WHERE fdc_id IS NOT NULL;

-- Food nutrients (100g normalized macros)
-- Note: Column names match Render production DB schema
CREATE TABLE IF NOT EXISTS food_nutrients_100g (
    id SERIAL PRIMARY KEY,
    food_id INTEGER NOT NULL REFERENCES food_items(id) ON DELETE CASCADE,
    calories_kcal DECIMAL(10, 2),     -- Calories per 100g
    protein_g DECIMAL(10, 2),         -- Protein per 100g
    fat_g DECIMAL(10, 2),             -- Total fat per 100g
    carbs_g DECIMAL(10, 2),           -- Total carbs per 100g
    fiber_g DECIMAL(10, 2),           -- Dietary fiber per 100g
    sugar_g DECIMAL(10, 2),           -- Total sugars per 100g
    sodium_mg DECIMAL(10, 2),         -- Sodium per 100g
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(food_id)
);

CREATE INDEX idx_food_nutrients_food_id ON food_nutrients_100g(food_id);

-- Turkish localization for food items
CREATE TABLE IF NOT EXISTS food_localization_tr (
    id SERIAL PRIMARY KEY,
    food_id INTEGER NOT NULL REFERENCES food_items(id) ON DELETE CASCADE,
    name_tr VARCHAR(500) NOT NULL,
    aliases_tr TEXT[],  -- Array of Turkish aliases/search terms
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(food_id)
);

CREATE INDEX idx_food_localization_tr_name ON food_localization_tr(name_tr);
CREATE INDEX idx_food_localization_tr_food_id ON food_localization_tr(food_id);

-- GIN index for array search on aliases_tr
CREATE INDEX idx_food_localization_tr_aliases ON food_localization_tr USING GIN(aliases_tr);

COMMENT ON TABLE food_items IS 'Food items from USDA FoodData Central and custom entries';
COMMENT ON TABLE food_nutrients_100g IS 'Macronutrients normalized to 100g servings';
COMMENT ON TABLE food_localization_tr IS 'Turkish translations and search aliases for food items';
