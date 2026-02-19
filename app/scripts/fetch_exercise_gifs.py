"""
ExerciseDB GIF URL Matcher

Fetches exercises from ExerciseDB open-source API (v1),
fuzzy-matches them with our exercise_library table,
and updates gif_url column.

Usage:
    python -m app.scripts.fetch_exercise_gifs

ExerciseDB v1 (open source): https://exercisedb.io
Response format: { id, name, bodyPart, target, equipment, gifUrl, ... }
"""

import os
import re
import json
import psycopg2
import urllib.request
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fithub_db_8rja_user:ysyQgMZ0i3Tky5CI5214yTpdlwUl4ky0@dpg-d59gokumcj7s73f7i760-a.frankfurt-postgres.render.com/fithub_db_8rja"
)

# ExerciseDB open-source API v1
EXERCISEDB_API_URL = "https://exercisedb.p.rapidapi.com/exercises?limit=1500&offset=0"
# Alternative: v1 open source (no API key needed)
EXERCISEDB_V1_URL = "https://v1.exercisedb.io/api/v1/exercises?limit=1500&offset=0"


def normalize(s: str) -> str:
    """Normalize exercise name for matching."""
    return re.sub(r'[^a-z0-9]', '', s.lower().strip())


def fetch_exercisedb_data():
    """Fetch all exercises from ExerciseDB API."""

    # Try v1 open source first (no API key needed)
    urls_to_try = [
        ("v1", EXERCISEDB_V1_URL, {}),
    ]

    # If RapidAPI key is available, try that too
    rapid_api_key = os.getenv("RAPIDAPI_KEY")
    if rapid_api_key:
        urls_to_try.insert(0, ("rapidapi", EXERCISEDB_API_URL, {
            "X-RapidAPI-Key": rapid_api_key,
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com"
        }))

    for source, url, headers in urls_to_try:
        try:
            print(f"Trying {source}: {url}")
            req = urllib.request.Request(url)
            for k, v in headers.items():
                req.add_header(k, v)

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())

            if isinstance(data, list) and len(data) > 0:
                print(f"  -> Got {len(data)} exercises from {source}")
                return data
            elif isinstance(data, dict) and "data" in data:
                exercises = data["data"]
                print(f"  -> Got {len(exercises)} exercises from {source}")
                return exercises
            else:
                print(f"  -> Unexpected response format from {source}")

        except Exception as e:
            print(f"  -> Failed: {e}")

    return None


def load_local_exercisedb():
    """Fallback: load from local free-exercise-db clone if API fails."""
    local_path = os.getenv("EXERCISE_DB_PATH", "./free-exercise-db/exercises")

    if not os.path.isdir(local_path):
        # Try alternate paths
        for alt in [
            "/Users/eraykucuk/Desktop/fithub-all/fithub-backend/free-exercise-db/exercises",
            os.path.join(os.path.dirname(__file__), "../../free-exercise-db/exercises"),
        ]:
            if os.path.isdir(alt):
                local_path = alt
                break

    if not os.path.isdir(local_path):
        return None

    print(f"Loading from local: {local_path}")
    exercises = []

    for ex_id in os.listdir(local_path):
        ex_dir = os.path.join(local_path, ex_id)
        json_path = os.path.join(ex_dir, "exercise.json") if os.path.isdir(ex_dir) else None
        if not json_path or not os.path.isfile(json_path):
            json_path = os.path.join(local_path, f"{ex_id}.json")
        if not os.path.isfile(json_path):
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["id"] = ex_id
        exercises.append(data)

    print(f"  -> Loaded {len(exercises)} exercises locally")
    return exercises


def main():
    # Step 1: Get ExerciseDB data
    print("=" * 60)
    print("ExerciseDB GIF URL Matcher")
    print("=" * 60)

    edb_data = fetch_exercisedb_data()

    if not edb_data:
        print("API failed, trying local dataset...")
        edb_data = load_local_exercisedb()

    if not edb_data:
        print("ERROR: Could not get ExerciseDB data from API or local.")
        print("Options:")
        print("  1. Set RAPIDAPI_KEY env var for RapidAPI access")
        print("  2. Clone free-exercise-db repo and set EXERCISE_DB_PATH")
        return

    # Build lookup: normalized_name -> gifUrl
    edb_lookup = {}
    for ex in edb_data:
        name = ex.get("name", "")
        gif_url = ex.get("gifUrl", "")
        ex_id = ex.get("id", "")

        if name and gif_url:
            norm = normalize(name)
            edb_lookup[norm] = gif_url

        # Also index by ID
        if ex_id and gif_url:
            edb_lookup[str(ex_id)] = gif_url

    print(f"\nExerciseDB lookup table: {len(edb_lookup)} entries with GIF URLs")

    # Step 2: Connect to DB
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Step 3: Get our exercises
    cur.execute("""
        SELECT id, external_id, canonical_name, image_urls, gif_url
        FROM exercise_library
        ORDER BY id
    """)
    our_exercises = cur.fetchall()
    print(f"Our exercise_library: {len(our_exercises)} exercises")

    # Step 4: Match and update
    matched = 0
    unmatched = []
    already_has_gif = 0

    for ex in our_exercises:
        # Skip if already has gif_url
        if ex.get("gif_url"):
            already_has_gif += 1
            continue

        canonical = ex["canonical_name"] or ""
        external_id = ex["external_id"] or ""
        norm_name = normalize(canonical)

        # Try matching strategies
        gif_url = None

        # 1. Exact normalized name match
        if norm_name in edb_lookup:
            gif_url = edb_lookup[norm_name]

        # 2. Try external_id as key
        if not gif_url and external_id:
            norm_ext = normalize(external_id)
            if norm_ext in edb_lookup:
                gif_url = edb_lookup[norm_ext]

        # 3. Try external_id with underscores replaced
        if not gif_url and external_id:
            alt = external_id.replace("_", " ").replace("-", " ")
            norm_alt = normalize(alt)
            if norm_alt in edb_lookup:
                gif_url = edb_lookup[norm_alt]

        if gif_url:
            cur.execute(
                "UPDATE exercise_library SET gif_url = %s WHERE id = %s",
                (gif_url, ex["id"])
            )
            matched += 1
        else:
            unmatched.append(canonical)

    conn.commit()

    # Report
    print(f"\n{'=' * 60}")
    print(f"Results:")
    print(f"  Already had GIF:  {already_has_gif}")
    print(f"  Newly matched:    {matched}")
    print(f"  Unmatched:        {len(unmatched)}")
    print(f"  Total:            {len(our_exercises)}")
    print(f"{'=' * 60}")

    if unmatched and len(unmatched) <= 50:
        print(f"\nUnmatched exercises:")
        for name in unmatched[:50]:
            print(f"  - {name}")
    elif unmatched:
        print(f"\nFirst 50 unmatched exercises:")
        for name in unmatched[:50]:
            print(f"  - {name}")
        print(f"  ... and {len(unmatched) - 50} more")

    cur.close()
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
