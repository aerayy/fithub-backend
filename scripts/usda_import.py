#!/usr/bin/env python3
"""
USDA FoodData Central API importer with Turkish translation support

Downloads food data from USDA and imports to PostgreSQL with optional
AI-powered Turkish translation using OpenAI GPT.

Usage:
    # With Turkish translation (default)
    python scripts/usda_import.py --search "chicken breast" --limit 10

    # Without translation (faster, English only)
    python scripts/usda_import.py --search "chicken" --limit 20 --no-translate

    # Batch import common fitness foods
    python scripts/usda_import.py --batch-fitness

Requirements:
    - USDA_API_KEY: Get free key at https://fdc.nal.usda.gov/api-key-signup.html
    - OPENAI_API_KEY: For Turkish translation (optional if --no-translate)
    - DATABASE_URL or DB_* env vars for PostgreSQL connection
"""
import os
import sys
import json
import time
import argparse
import requests
import psycopg2
from dotenv import load_dotenv

# Load .env from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env"))

# API configs
USDA_API_KEY = os.getenv("USDA_API_KEY", "")
USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL")

# DB config fallback
DB_NAME = os.getenv("DB_NAME", "fithub")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Eray123!")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))

# USDA nutrient IDs (FoodData Central standard)
NUTRIENT_MAP = {
    "Energy": 1008,
    "Protein": 1003,
    "Total lipid (fat)": 1004,
    "Carbohydrate, by difference": 1005,
    "Fiber, total dietary": 1079,
    "Sugars, total including NLEA": 2000,
    "Sodium, Na": 1093,
}

# Common fitness foods for batch import
FITNESS_FOODS = [
    # Proteins
    "chicken breast", "chicken thigh", "turkey breast", "beef steak",
    "ground beef", "salmon", "tuna", "tilapia", "shrimp", "egg",
    "egg white", "greek yogurt", "cottage cheese", "whey protein",
    # Carbs
    "rice", "brown rice", "oatmeal", "quinoa", "sweet potato",
    "potato", "pasta", "bread", "banana", "apple",
    # Vegetables
    "broccoli", "spinach", "asparagus", "green beans", "cucumber",
    "tomato", "carrot", "bell pepper", "lettuce", "onion",
    # Fats & Dairy
    "avocado", "olive oil", "almond", "peanut butter", "cheese",
    "milk", "butter", "coconut oil",
    # Fruits
    "orange", "strawberry", "blueberry", "watermelon", "grape",
]


def translate_food_with_gpt(name_en: str, api_key: str) -> dict:
    """
    Use OpenAI GPT to translate and clean food name to Turkish.
    
    Returns: {"name_tr": "...", "description_tr": "...", "aliases_tr": [...]}
    """
    if not api_key:
        return None

    prompt = f"""Besin ismi (İngilizce): "{name_en}"

Bu besini Türkçe'ye çevir ve fitness/diyet uygulaması için uygun hale getir.

JSON formatında döndür:
{{
  "name_tr": "Temiz, kısa Türkçe isim (max 50 karakter)",
  "description_tr": "Kısa açıklama (1 cümle, max 100 karakter)",
  "aliases_tr": ["arama", "terimleri", "için", "alternatif", "isimler"]
}}

Kurallar:
- name_tr: Sade ve anlaşılır olsun (örn: "Tavuk Göğsü" veya "Yulaf Ezmesi")
- description_tr: Pişirme durumu veya özelliği belirt (çiğ/pişmiş, derisiz vb.)
- aliases_tr: Türkçe ve yaygın kullanılan arama terimleri (3-5 adet)
- Sadece JSON döndür, başka metin ekleme"""

    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 300,
            },
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        
        # Parse JSON from response
        # Handle markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        return json.loads(content.strip())
    except Exception as e:
        print(f"  ⚠️ Translation failed: {e}")
        return None


def search_usda_foods(query: str, page_size: int = 10, api_key: str = ""):
    """Search USDA FoodData Central API"""
    if not api_key:
        raise ValueError("USDA_API_KEY not set")

    params = {
        "api_key": api_key,
        "query": query,
        "pageSize": page_size,
        "dataType": ["Foundation", "SR Legacy"],
    }

    resp = requests.get(USDA_SEARCH_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("foods", [])


def extract_nutrients_100g(usda_food: dict) -> dict:
    """Extract and normalize nutrients to 100g base"""
    nutrients = {
        "calories_kcal": None,
        "protein_g": None,
        "fat_g": None,
        "carbs_g": None,
        "fiber_g": None,
        "sugar_g": None,
        "sodium_mg": None,
    }

    for nutrient in usda_food.get("foodNutrients", []):
        nid = nutrient.get("nutrientId")
        val = nutrient.get("value")
        if val is None:
            continue

        if nid == NUTRIENT_MAP["Energy"]:
            nutrients["calories_kcal"] = round(float(val), 2)
        elif nid == NUTRIENT_MAP["Protein"]:
            nutrients["protein_g"] = round(float(val), 2)
        elif nid == NUTRIENT_MAP["Total lipid (fat)"]:
            nutrients["fat_g"] = round(float(val), 2)
        elif nid == NUTRIENT_MAP["Carbohydrate, by difference"]:
            nutrients["carbs_g"] = round(float(val), 2)
        elif nid == NUTRIENT_MAP["Fiber, total dietary"]:
            nutrients["fiber_g"] = round(float(val), 2)
        elif nid == NUTRIENT_MAP["Sugars, total including NLEA"]:
            nutrients["sugar_g"] = round(float(val), 2)
        elif nid == NUTRIENT_MAP["Sodium, Na"]:
            nutrients["sodium_mg"] = round(float(val), 2)

    return nutrients


def import_to_db(foods: list, db_conn, translate: bool = True):
    """
    Import foods to food_items + food_nutrients_100g + food_localization_tr
    
    Args:
        foods: List of USDA food dicts
        db_conn: PostgreSQL connection
        translate: If True, use GPT to translate to Turkish
    """
    cur = db_conn.cursor()
    imported = 0
    skipped = 0
    translated = 0

    for i, food in enumerate(foods):
        fdc_id = food.get("fdcId")
        description = food.get("description", "")
        data_type = food.get("dataType", "")

        if not fdc_id or not description:
            skipped += 1
            continue

        nutrients = extract_nutrients_100g(food)

        try:
            # 1) Insert food_items
            cur.execute(
                """
                INSERT INTO food_items (fdc_id, name_en, description, data_type, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (fdc_id) DO NOTHING
                RETURNING id
                """,
                (fdc_id, description[:500], description, data_type),
            )
            result = cur.fetchone()

            if not result:
                skipped += 1
                continue

            food_id = result[0]

            # 2) Insert nutrients
            cur.execute(
                """
                INSERT INTO food_nutrients_100g (
                    food_id, calories_kcal, protein_g, fat_g, carbs_g,
                    fiber_g, sugar_g, sodium_mg, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (food_id) DO UPDATE SET
                    calories_kcal = EXCLUDED.calories_kcal,
                    protein_g = EXCLUDED.protein_g,
                    fat_g = EXCLUDED.fat_g,
                    carbs_g = EXCLUDED.carbs_g,
                    fiber_g = EXCLUDED.fiber_g,
                    sugar_g = EXCLUDED.sugar_g,
                    sodium_mg = EXCLUDED.sodium_mg,
                    updated_at = NOW()
                """,
                (
                    food_id,
                    nutrients["calories_kcal"],
                    nutrients["protein_g"],
                    nutrients["fat_g"],
                    nutrients["carbs_g"],
                    nutrients["fiber_g"],
                    nutrients["sugar_g"],
                    nutrients["sodium_mg"],
                ),
            )

            # 3) Translate and insert Turkish localization
            if translate and OPENAI_API_KEY:
                print(f"  🔄 Translating: {description[:50]}...")
                tr_data = translate_food_with_gpt(description, OPENAI_API_KEY)
                
                if tr_data:
                    cur.execute(
                        """
                        INSERT INTO food_localization_tr (
                            food_id, name_tr, description_tr, aliases_tr, is_active
                        )
                        VALUES (%s, %s, %s, %s, TRUE)
                        ON CONFLICT (food_id) DO UPDATE SET
                            name_tr = EXCLUDED.name_tr,
                            description_tr = EXCLUDED.description_tr,
                            aliases_tr = EXCLUDED.aliases_tr
                        """,
                        (
                            food_id,
                            tr_data.get("name_tr", description[:100]),
                            tr_data.get("description_tr"),
                            tr_data.get("aliases_tr", []),
                        ),
                    )
                    translated += 1
                    print(f"  ✅ {tr_data.get('name_tr', 'N/A')}")
                
                # Rate limiting for GPT API
                time.sleep(0.3)

            imported += 1
            print(f"✅ [{i+1}/{len(foods)}] Imported: {description[:50]} (FDC: {fdc_id})")

        except Exception as e:
            print(f"❌ Error: {description[:40]}: {e}")
            db_conn.rollback()
            skipped += 1
            continue

    db_conn.commit()
    print(f"\n📊 Import complete: {imported} imported, {translated} translated, {skipped} skipped")


def main():
    parser = argparse.ArgumentParser(
        description="Import foods from USDA FoodData Central with Turkish translation"
    )
    parser.add_argument("--search", help="Search query (e.g. 'chicken breast')")
    parser.add_argument("--limit", type=int, default=5, help="Max results per search (default: 5)")
    parser.add_argument(
        "--no-translate",
        action="store_true",
        help="Skip Turkish translation (faster, English only)"
    )
    parser.add_argument(
        "--batch-fitness",
        action="store_true",
        help="Import common fitness foods (predefined list)"
    )
    args = parser.parse_args()

    # Validate required args
    if not args.search and not args.batch_fitness:
        parser.error("Either --search or --batch-fitness is required")

    # Validate API keys
    if not USDA_API_KEY:
        print("❌ Error: USDA_API_KEY not set")
        print("Get free API key: https://fdc.nal.usda.gov/api-key-signup.html")
        sys.exit(1)

    translate = not args.no_translate
    if translate and not OPENAI_API_KEY:
        print("⚠️ Warning: OPENAI_API_KEY not set, skipping Turkish translation")
        translate = False

    # Connect to DB
    try:
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            print("✅ Connected to DB via DATABASE_URL")
        else:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
            )
            print(f"✅ Connected to DB: {DB_NAME}@{DB_HOST}:{DB_PORT}")
    except Exception as e:
        print(f"❌ DB connection failed: {e}")
        sys.exit(1)

    # Build search list
    if args.batch_fitness:
        searches = FITNESS_FOODS
        print(f"\n🏋️ Batch importing {len(searches)} fitness food categories...")
    else:
        searches = [args.search]

    total_imported = 0
    
    for query in searches:
        print(f"\n🔍 Searching USDA for: '{query}' (limit: {args.limit})")
        try:
            foods = search_usda_foods(query, page_size=args.limit, api_key=USDA_API_KEY)
            print(f"✅ Found {len(foods)} foods")
        except Exception as e:
            print(f"❌ USDA API error for '{query}': {e}")
            continue

        if foods:
            print(f"\n📥 Importing {len(foods)} foods...")
            import_to_db(foods, conn, translate=translate)
            total_imported += len(foods)
        
        # Small delay between searches
        if len(searches) > 1:
            time.sleep(0.5)

    conn.close()
    print(f"\n✅ Done! Total foods processed: {total_imported}")


if __name__ == "__main__":
    main()
