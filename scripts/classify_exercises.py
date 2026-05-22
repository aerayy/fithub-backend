from __future__ import annotations

"""Batch-classify exercise_library rows with the metadata Workout Generator v3
needs (movement_pattern, fatigue_score, stability, complexity, gender_skew,
goal_tags, equipment_*, unilateral).

Uses gpt-4.1-mini + strict JSON Schema enum so the model can't invent values.

Usage:
    cd fithub-backend
    python3 scripts/classify_exercises.py --limit 20 --dry-run        # sample run
    python3 scripts/classify_exercises.py --limit 100                 # write to DB
    python3 scripts/classify_exercises.py --all                       # full batch
    python3 scripts/classify_exercises.py --refill                    # re-classify NULLs only

Idempotent: by default refills only rows with NULL movement_pattern. Pass
--force to re-classify everything (e.g. after rule tweak).

Cost: ~$0.01 / 100 exercises @ gpt-4.1-mini. Full 2185 = ~$0.22.

Outputs:
    scripts/classify_output/exercise_metadata_YYYYMMDD_HHMMSS.csv
    (human review — verify edge cases before bulk commit)
"""
import argparse
import asyncio
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import AsyncOpenAI
except ImportError:
    print("ERROR: openai required. pip install openai", file=sys.stderr)
    sys.exit(1)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
except ImportError:
    print("ERROR: psycopg2 required.", file=sys.stderr)
    sys.exit(1)


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────
#  Enum vocabulary — strict, AI can't invent
# ────────────────────────────────────────────────────────────────────────
MOVEMENT_PATTERNS = [
    "horizontal_press", "vertical_press",
    "horizontal_pull", "vertical_pull",
    "squat", "hinge", "lunge", "carry",
    "rotation", "anti_rotation", "anti_extension",
    "iso_curl", "iso_extension", "iso_fly", "iso_raise",
    "iso_shrug", "iso_calf", "iso_wrist",
    "explosive", "gait", "stretch_mobility",
    "other",
]
STABILITY = ["free", "machine", "cable", "bodyweight", "smith", "band"]
GENDER_SKEW = ["neutral", "female_favored", "male_favored"]
GOAL_TAGS = ["hypertrophy", "strength", "power", "endurance", "mobility", "fat_loss"]
EQUIPMENT_TOKENS = [
    "barbell", "dumbbell", "machine", "cable", "kettlebell", "bodyweight",
    "smith", "bench", "rack", "pull_up_bar", "ez_bar", "band", "resistance_band",
    "ab_wheel", "trap_bar", "landmine", "medicine_ball", "trx", "dip_bar",
    "incline_bench", "decline_bench", "preacher_bench", "leg_press",
    "leg_curl_machine", "leg_extension_machine", "lat_pulldown",
    "seated_row_machine", "cable_crossover", "hip_thrust_pad",
]


# ────────────────────────────────────────────────────────────────────────
#  JSON Schema for the LLM response
# ────────────────────────────────────────────────────────────────────────
def build_schema(batch_size: int) -> dict:
    """Strict schema: array of `batch_size` items, each item is the metadata
    block for an exercise. Order matches input order."""
    return {
        "type": "object",
        "properties": {
            "exercises": {
                "type": "array",
                "minItems": batch_size,
                "maxItems": batch_size,
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "movement_pattern": {"type": "string", "enum": MOVEMENT_PATTERNS},
                        "fatigue_score": {"type": "integer", "minimum": 1, "maximum": 10},
                        "stability": {"type": "string", "enum": STABILITY},
                        "unilateral": {"type": "boolean"},
                        "complexity": {"type": "integer", "minimum": 1, "maximum": 5},
                        "gender_skew": {"type": "string", "enum": GENDER_SKEW},
                        "goal_tags": {
                            "type": "array",
                            "items": {"type": "string", "enum": GOAL_TAGS},
                            "minItems": 1,
                            "maxItems": 4,
                        },
                        "equipment_required": {
                            "type": "array",
                            "items": {"type": "string", "enum": EQUIPMENT_TOKENS},
                            "minItems": 1,
                            "maxItems": 4,
                        },
                        "equipment_alternative": {
                            "type": "array",
                            "items": {"type": "string", "enum": EQUIPMENT_TOKENS},
                            "minItems": 0,
                            "maxItems": 4,
                        },
                    },
                    "required": [
                        "id", "movement_pattern", "fatigue_score", "stability",
                        "unilateral", "complexity", "gender_skew", "goal_tags",
                        "equipment_required", "equipment_alternative",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["exercises"],
        "additionalProperties": False,
    }


SYSTEM_PROMPT = """Sen IFBB Pro standartlarında 20+ yıllık deneyimli bir
fitness koçusun. Görevin: verilen egzersizleri yapısal metadata ile
sınıflandırmak.

Kurallar:
- movement_pattern: en spesifik ana hareket deseni. Mesela:
    "Bench Press" → horizontal_press
    "Overhead Press" → vertical_press
    "Bent Over Row" → horizontal_pull
    "Pull-Up" → vertical_pull
    "Back Squat" → squat
    "Deadlift / RDL" → hinge
    "Bulgarian Split Squat" → lunge
    "Barbell Curl" → iso_curl
    "Tricep Pushdown" → iso_extension
    "Cable Fly / Pec Deck" → iso_fly
    "Lateral Raise" → iso_raise
    "Plank" → anti_extension
    "Pallof Press" → anti_rotation
    "Calf Raise" → iso_calf
    "Standing Calf Raise" → iso_calf
    "Farmer Carry" → carry
    "Box Jump / Power Clean" → explosive
    "Mobility / Foam Roll" → stretch_mobility

- fatigue_score: 1-10. Ağır barbell compound = 8-10. Cable/machine isolation = 2-3.
  Deadlift/Squat/Power Clean = 9-10. Lateral Raise = 2.

- stability: hareket nasıl yapılıyor? Barbell/Dumbbell free = "free".
  Cable column = "cable". Selectorized machine = "machine".
  Smith machine = "smith". Bodyweight (push-up/pull-up/dip) = "bodyweight".
  Band = "band".

- unilateral: tek tarafla yapılıyor mu? Dumbbell row, single-leg deadlift,
  Bulgarian split squat, lunge → TRUE. Bench press, squat, deadlift → FALSE.

- complexity: 1-5 skill ceiling.
    1 = leg extension, leg curl, cable lateral raise (pure isolation, az risk)
    2 = dumbbell row, lat pulldown, bench press
    3 = barbell row, deadlift (technique critical)
    4 = front squat, weighted pull-up, snatch grip dl, jefferson curl
    5 = snatch, clean & jerk, overhead squat (Olympic / very technical)
  Beginner cap = 2, intermediate cap = 4, advanced = any.

- gender_skew: çoğunlukla neutral. female_favored = glute kick-back, hip
  thrust, side step-up, hip abduction. male_favored = sırf çok ağır CNS
  yükleyen advanced barbell varyasyonları (rare). DEFAULT = neutral.

- goal_tags: birden çok seçebilirsin. Powerlifting compound → strength.
  Bodybuilding isolation → hypertrophy. Explosive lift → power.
  Foam roll / mobility → mobility. Burpee / sled push → endurance, fat_loss.

- equipment_required: hareketi yapmak için zorunlu equipment. enum tokenları
  kullan. Örnek: "Bench Press" → ["barbell","bench"]; "Cable Fly" →
  ["cable"]; "Pull-Up" → ["pull_up_bar","bodyweight"]; "Dumbbell Row" →
  ["dumbbell"].

- equipment_alternative: aynı hareketin başka equipment ile yapılabilirliği.
  "Bench Press" → ["dumbbell","smith"]. "Pull-Up" → ["lat_pulldown"].

ÇOK ÖNEMLİ: id alanı input'taki id ile birebir aynı kalacak. Hiçbirini
karıştırma, hiçbirini atla. Sıra input ile aynı. Sadece JSON döndür.
"""


def build_user_prompt(rows: list[dict]) -> str:
    parts = ["Aşağıdaki egzersizleri sınıflandır. Her satır = bir egzersiz.\n"]
    for r in rows:
        muscles = ", ".join((r.get("primary_muscles") or [])[:3]) or "—"
        equip = r.get("equipment") or "—"
        level = r.get("level") or "—"
        parts.append(
            f"- id={r['id']} | name=\"{r['canonical_name']}\" | "
            f"primary_muscles=[{muscles}] | equipment=\"{equip}\" | level=\"{level}\""
        )
    return "\n".join(parts)


# ────────────────────────────────────────────────────────────────────────
#  DB helpers
# ────────────────────────────────────────────────────────────────────────
def db_connect():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "fithub"),
    )


def fetch_targets(conn, force: bool, limit: int | None) -> list[dict]:
    """Pull rows that need classification."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    where = "" if force else "WHERE movement_pattern IS NULL"
    lim = f"LIMIT {int(limit)}" if limit else ""
    cur.execute(f"""
        SELECT id, canonical_name, primary_muscles, secondary_muscles,
               equipment, level
        FROM exercise_library
        {where}
        ORDER BY id
        {lim}
    """)
    return cur.fetchall()


def write_back(conn, results: list[dict]) -> int:
    """Update exercise_library with classified metadata."""
    cur = conn.cursor()
    n = 0
    for r in results:
        cur.execute("""
            UPDATE exercise_library
            SET movement_pattern = %(movement_pattern)s,
                fatigue_score    = %(fatigue_score)s,
                stability        = %(stability)s,
                unilateral       = %(unilateral)s,
                complexity       = %(complexity)s,
                gender_skew      = CASE WHEN %(gender_skew)s = 'neutral'
                                        THEN NULL ELSE %(gender_skew)s END,
                goal_tags        = %(goal_tags)s,
                equipment_required    = %(equipment_required)s,
                equipment_alternative = %(equipment_alternative)s
            WHERE id = %(id)s
        """, r)
        n += cur.rowcount
    conn.commit()
    return n


# ────────────────────────────────────────────────────────────────────────
#  LLM batch
# ────────────────────────────────────────────────────────────────────────
async def classify_batch(client: AsyncOpenAI, rows: list[dict]) -> list[dict]:
    schema = build_schema(len(rows))
    response = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(rows)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "exercise_metadata_batch",
                "schema": schema,
                "strict": True,
            },
        },
        temperature=0.1,
        max_tokens=8000,
    )
    raw = response.choices[0].message.content
    payload = json.loads(raw)
    return payload["exercises"]


async def run(args):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        logger.error("OPENAI_API_KEY missing")
        sys.exit(1)

    client = AsyncOpenAI(api_key=api_key, timeout=120.0, max_retries=2)
    conn = db_connect()

    targets = fetch_targets(conn, force=args.force, limit=args.limit if not args.all else None)
    logger.info("targets=%d (force=%s, dry_run=%s)", len(targets), args.force, args.dry_run)
    if not targets:
        logger.info("nothing to classify — exit")
        return

    out_dir = Path(__file__).parent / "classify_output"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    csv_path = out_dir / f"exercise_metadata_{ts}.csv"
    csv_file = open(csv_path, "w", newline="", encoding="utf-8")
    writer = csv.writer(csv_file)
    writer.writerow([
        "id", "name", "movement_pattern", "fatigue_score", "stability",
        "unilateral", "complexity", "gender_skew", "goal_tags",
        "equipment_required", "equipment_alternative",
    ])

    batch_size = args.batch_size
    total_ok = 0
    name_by_id = {r["id"]: r["canonical_name"] for r in targets}

    for i in range(0, len(targets), batch_size):
        batch = targets[i:i + batch_size]
        try:
            t0 = time.time()
            classified = await classify_batch(client, batch)
            dt = time.time() - t0
            logger.info("batch %d/%d → %d items in %.1fs",
                        i // batch_size + 1,
                        (len(targets) + batch_size - 1) // batch_size,
                        len(classified), dt)
        except Exception as e:
            logger.exception("batch fail: %s", e)
            continue

        # Pydantic-like sanity: id'ler input ile eşleşmeli (LLM bazen karıştırır)
        input_ids = {r["id"] for r in batch}
        for c in classified:
            if c["id"] not in input_ids:
                logger.warning("phantom id %s — skipping", c["id"])
                continue
            writer.writerow([
                c["id"], name_by_id.get(c["id"], "?"),
                c["movement_pattern"], c["fatigue_score"], c["stability"],
                c["unilateral"], c["complexity"], c["gender_skew"],
                "|".join(c["goal_tags"]),
                "|".join(c["equipment_required"]),
                "|".join(c["equipment_alternative"]),
            ])

        if not args.dry_run:
            updated = write_back(conn, classified)
            total_ok += updated
            logger.info("  ↳ wrote %d rows to DB", updated)

    csv_file.close()
    conn.close()

    print("")
    print("=" * 60)
    print(f"CSV  → {csv_path}")
    if args.dry_run:
        print("Dry run — DB UNCHANGED. Review CSV then re-run without --dry-run.")
    else:
        print(f"DB updated: {total_ok} rows.")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20, help="rows to classify (default 20)")
    parser.add_argument("--all", action="store_true", help="ignore --limit, do all")
    parser.add_argument("--force", action="store_true", help="re-classify even non-NULL rows")
    parser.add_argument("--dry-run", action="store_true", help="CSV only, no DB write")
    parser.add_argument("--batch-size", type=int, default=20, help="exercises per LLM call")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
