"""
Heal broken workout_exercises rows.

Sadece kirli row'lara dokunur:
  - exercise_library_id IS NULL, veya
  - bağlı exercise_library satırının gif_url'i NULL/empty

Her kirli row için matcher'ı çalıştırır, doğru library_id'yi atar.
exercise_name (koçun/AI'ın yazdığı isim) DEĞİŞTİRİLMEZ.

Usage:
  DRY_RUN=1 python scripts/heal_broken_exercises.py   # değişiklik yapmaz, raporlar
  python scripts/heal_broken_exercises.py             # gerçekten günceller
"""
import os
import sys

# Backend path'i ekle ki app.api.coach.routes import edebilelim
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor

from app.api.coach.routes import _match_exercise_library

DRY_RUN = os.environ.get("DRY_RUN") == "1"

DSN = os.environ.get("DATABASE_URL") or (
    "postgresql://fithub_db_8rja_user:ysyQgMZ0i3Tky5CI5214yTpdlwUl4ky0"
    "@dpg-d59gokumcj7s73f7i760-a.frankfurt-postgres.render.com"
    "/fithub_db_8rja?sslmode=require"
)


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT we.id, we.exercise_name, we.exercise_library_id,
               wp.id AS program_id, wp.is_active, wp.client_user_id
        FROM workout_exercises we
        LEFT JOIN exercise_library el ON el.id = we.exercise_library_id
        JOIN workout_days wd ON wd.id = we.workout_day_id
        JOIN workout_programs wp ON wp.id = wd.workout_program_id
        WHERE we.exercise_library_id IS NULL
           OR el.gif_url IS NULL
           OR el.gif_url = ''
        ORDER BY wp.is_active DESC, wp.id DESC
        """
    )
    broken = cur.fetchall()

    print(f"Mode: {'DRY_RUN (no UPDATE)' if DRY_RUN else 'LIVE (will UPDATE)'}")
    print(f"Bulunan kirik row sayisi: {len(broken)}")
    print("=" * 80)

    healed_count = 0
    for row in broken:
        ex_id = row["id"]
        name = row["exercise_name"] or ""
        old_lib = row["exercise_library_id"]
        active = row["is_active"]

        matched = _match_exercise_library(cur, name)
        if matched is None:
            print(
                f"  ⚠ ex_id={ex_id} '{name}' — matcher None dondu (atliyorum)"
            )
            continue

        new_lib_id = matched["id"]
        new_name = matched["canonical_name"]
        active_flag = "[AKTIF]" if active else "[pasif]"

        print(
            f"  {active_flag} ex_id={ex_id} '{name}' "
            f"lib={old_lib} → {new_lib_id} (matched='{new_name}')"
        )

        if not DRY_RUN:
            cur.execute(
                "UPDATE workout_exercises SET exercise_library_id = %s WHERE id = %s",
                (new_lib_id, ex_id),
            )
            healed_count += 1

    if not DRY_RUN:
        conn.commit()
        print(f"\n✓ Healed {healed_count} rows committed.")
    else:
        print(f"\n(DRY_RUN — nothing committed. Set DRY_RUN=0 or unset to apply.)")

    cur.execute(
        """
        SELECT COUNT(*)
        FROM workout_exercises we
        LEFT JOIN exercise_library el ON el.id = we.exercise_library_id
        JOIN workout_days wd ON wd.id = we.workout_day_id
        JOIN workout_programs wp ON wp.id = wd.workout_program_id
        WHERE wp.is_active = TRUE
          AND (we.exercise_library_id IS NULL OR el.gif_url IS NULL OR el.gif_url = '')
        """
    )
    remaining = cur.fetchone()["count"]
    print(f"\nAktif programlardaki kalan kirik sayi: {remaining}")

    conn.close()


if __name__ == "__main__":
    main()
