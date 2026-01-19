import os
import json
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = "postgresql://fithub_db_8rja_user:ysyQgMZ0i3Tky5CI5214yTpdlwUl4ky0@dpg-d59gokumcj7s73f7i760-a.frankfurt-postgres.render.com/fithub_db_8rja"
EXERCISE_DB_PATH="/Users/eraykucuk/Desktop/fithub-all/fithub-backend/free-exercise-db" \

if not DATABASE_URL:
    raise SystemExit("❌ DATABASE_URL env variable is not set")


# 2) dataset path (git clone yaptığın yer)
DATASET_ROOT = os.getenv("EXERCISE_DB_PATH", "./free-exercise-db/exercises")

# 3) github raw image prefix
RAW_PREFIX = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"

def build_image_urls(external_id, images):
    # images: ["Air_Bike/0.jpg","Air_Bike/1.jpg"] ya da bazen sadece ["0.jpg","1.jpg"]
    urls = []
    for img in images or []:
        if "/" in img:
            urls.append(RAW_PREFIX + img)
        else:
            urls.append(f"{RAW_PREFIX}{external_id}/{img}")
    return urls

def main():
    if not os.path.isdir(DATASET_ROOT):
        raise SystemExit(f"Dataset path not found: {DATASET_ROOT}")

    conn = psycopg2.connect(
    DATABASE_URL,
    sslmode="require"   # Render için önemli
)

    
    cur = conn.cursor()

    rows = []
    for ex_id in os.listdir(DATASET_ROOT):
        ex_dir = os.path.join(DATASET_ROOT, ex_id)
        if not os.path.isdir(ex_dir):
            continue

                # Dataset iki formatta olabiliyor:
        # A) exercises/<id>.json
        # B) exercises/<id>/exercise.json

        json_path_a = os.path.join(DATASET_ROOT, f"{ex_id}.json")
        json_path_b = os.path.join(ex_dir, "exercise.json")

        json_path = None
        if os.path.isfile(json_path_a):
            json_path = json_path_a
        elif os.path.isfile(json_path_b):
            json_path = json_path_b
        else:
            continue


        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        external_id = ex_id
        name = data.get("name")
        if not name:
            continue

        level = data.get("level")
        equipment = data.get("equipment")
        category = data.get("category")
        primary = data.get("primaryMuscles") or []
        secondary = data.get("secondaryMuscles") or []
        instructions = data.get("instructions") or []
        images = data.get("images") or []
        image_urls = build_image_urls(external_id, images)

        rows.append((
            external_id,
            name,
            level,
            equipment,
            category,
            primary,
            secondary,
            instructions,
            image_urls,
        ))

    if not rows:
        raise SystemExit("No exercises found to import.")

    sql = """
    INSERT INTO exercise_library
      (external_id, canonical_name, level, equipment, category,
       primary_muscles, secondary_muscles, instructions, image_urls)
    VALUES %s
    ON CONFLICT (external_id) DO UPDATE SET
      canonical_name = EXCLUDED.canonical_name,
      level = EXCLUDED.level,
      equipment = EXCLUDED.equipment,
      category = EXCLUDED.category,
      primary_muscles = EXCLUDED.primary_muscles,
      secondary_muscles = EXCLUDED.secondary_muscles,
      instructions = EXCLUDED.instructions,
      image_urls = EXCLUDED.image_urls;
    """

    execute_values(cur, sql, rows, page_size=500)
    conn.commit()

    print(f"✅ Imported/updated: {len(rows)} exercises into exercise_library")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
