"""RAG matcher v2 — pulls similar BeGreens plans directly from Postgres rag_* tables.

Replaces the old JSON-file-based find_similar_programs. Uses real 13K+ coach plans
+ 23K user profiles imported from BeGreens dump.

Two flavors: nutrition (this module's original) and training (added below).
"""
from __future__ import annotations

import re
from typing import Optional
from psycopg2.extras import RealDictCursor


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_html(s: Optional[str]) -> str:
    """Strip the inline phpMyAdmin/TinyMCE markup that some BeGreens fields contain."""
    if not s:
        return ""
    return _HTML_TAG_RE.sub("", str(s)).strip()


def find_similar_nutrition_plans(
    db,
    age: int,
    weight_kg: float,
    height_cm: int,
    meal_count: int = 5,
    meal_count_window: int = 1,
    top_n: int = 3,
) -> list[dict]:
    """Return top-N nutrition plans whose user profile is closest to (age, weight, height).

    Score = 1.0 * |Δage| + 1.5 * |Δweight| + 0.5 * |Δheight|
    Filters:
      - profile must have age/weight/height parsed (~9K of 23K profiles)
      - plan must have meal_count ± 2 meals (so 5-meal target doesn't match a 9-meal plan)

    Returns list of dicts with: plan_id, profile_id, age, weight, height, sim_score, plan_name
    """
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        # Reasonable filtering windows around the student profile
        age_lo, age_hi = max(15, age - 8), min(80, age + 8)
        w_lo, w_hi = max(35.0, weight_kg - 15), min(200.0, weight_kg + 15)
        h_lo, h_hi = max(140, height_cm - 15), min(220, height_cm + 15)
        meal_lo = max(3, meal_count - meal_count_window)
        meal_hi = min(10, meal_count + meal_count_window)

        cur.execute(
            """
            WITH candidates AS (
                SELECT
                    np.id        AS plan_id,
                    np.name      AS plan_name,
                    p.id         AS profile_id,
                    p.age_int    AS age,
                    p.weight_kg  AS weight,
                    p.height_cm  AS height,
                    (abs(p.age_int - %s) * 1.0
                     + abs(COALESCE(p.weight_kg, %s) - %s) * 1.5
                     + abs(COALESCE(p.height_cm, %s) - %s) * 0.5) AS sim_score,
                    (SELECT COUNT(*) FROM rag_nutrition_meals m WHERE m.plan_id = np.id) AS meal_count
                FROM rag_nutrition_plans np
                JOIN rag_user_profiles p ON p.id = np.user_id
                WHERE p.age_int BETWEEN %s AND %s
                  AND p.weight_kg BETWEEN %s AND %s
                  AND p.height_cm BETWEEN %s AND %s
            )
            SELECT * FROM candidates
            WHERE meal_count BETWEEN %s AND %s
            ORDER BY sim_score ASC, plan_id DESC
            LIMIT %s;
            """,
            (
                age, weight_kg, weight_kg, height_cm, height_cm,
                age_lo, age_hi, w_lo, w_hi, h_lo, h_hi,
                meal_lo, meal_hi,
                top_n,
            ),
        )
        return cur.fetchall() or []
    finally:
        cur.close()


def fetch_plan_content(db, plan_id: int) -> list[dict]:
    """Return all meals + their foods for one plan, ordered by meal_time."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            SELECT
                m.id          AS meal_id,
                m.meal_name   AS meal_name,
                m.meal_time   AS meal_time,
                f.id          AS food_id,
                f.name        AS food_name,
                f.quantity    AS quantity,
                f.weight      AS unit
            FROM rag_nutrition_meals m
            LEFT JOIN rag_nutrition_foods f ON f.meal_id = m.id
            WHERE m.plan_id = %s
            ORDER BY m.meal_time ASC NULLS LAST, m.id ASC, f.id ASC;
            """,
            (plan_id,),
        )
        rows = cur.fetchall() or []
    finally:
        cur.close()

    # Group by meal
    meals_by_id: dict = {}
    meal_order: list = []
    for r in rows:
        mid = r["meal_id"]
        if mid not in meals_by_id:
            meals_by_id[mid] = {
                "meal_name": r["meal_name"],
                "meal_time": r["meal_time"].strftime("%H:%M") if r["meal_time"] else None,
                "foods": [],
            }
            meal_order.append(mid)
        if r.get("food_name"):
            meals_by_id[mid]["foods"].append({
                "name": r["food_name"],
                "quantity": float(r["quantity"]) if r["quantity"] is not None else None,
                "unit": r["unit"],
            })

    return [meals_by_id[mid] for mid in meal_order]


def format_plans_for_prompt(plans: list[dict], plan_contents: list[list[dict]]) -> str:
    """Build a compact text block listing 3 reference plans for the AI prompt."""
    lines = ["═══ KOÇUN BENZER PROFİLLERE YAZDIĞI 3 GERÇEK PROGRAM ═══"]
    for i, (plan, meals) in enumerate(zip(plans, plan_contents), start=1):
        lines.append("")
        lines.append(
            f"── REFERANS {i} (profil: {plan['age']} yaş, "
            f"{plan['weight']} kg, {plan['height']} cm; benzerlik={plan['sim_score']:.1f}) ──"
        )
        for m in meals:
            time_str = m["meal_time"] or "—"
            food_str = ", ".join(
                f"{f['name']} ({f['quantity']:g} {f['unit']})" if f.get("quantity") is not None
                else f["name"]
                for f in m["foods"]
            )
            lines.append(f"  {time_str}  {m['meal_name']}: {food_str}")
    lines.append("")
    lines.append("BU PROGRAMLARIN YAPISINI, ÖĞÜN ZAMANLAMASINI VE BESİN KOMBİNASYONLARINI REFERANS AL.")
    lines.append("Öğrencinin profiline uyarla — birebir kopyalama, koç tarzında yaz.")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
#  Training (workout) RAG
# ════════════════════════════════════════════════════════════════════════════

def find_similar_training_plans(
    db,
    age: int,
    weight_kg: float,
    height_cm: int,
    sessions_per_week: int = 4,
    sessions_window: int = 1,
    top_n: int = 3,
) -> list[dict]:
    """Top-N BeGreens training plans for profiles close to (age, weight, height).
    Also matches roughly on session frequency (kaç gün/hafta antrenman)."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        age_lo, age_hi = max(15, age - 8), min(80, age + 8)
        w_lo, w_hi = max(35.0, weight_kg - 15), min(200.0, weight_kg + 15)
        h_lo, h_hi = max(140, height_cm - 15), min(220, height_cm + 15)
        # Most BeGreens plans have ~3-6 sessions; widen if no exact match
        s_lo = max(2, sessions_per_week - sessions_window)
        s_hi = min(7, sessions_per_week + sessions_window)

        cur.execute(
            """
            WITH plan_session_count AS (
                SELECT tp.id AS plan_id, COUNT(s.id) AS session_count
                FROM rag_training_plans tp
                LEFT JOIN rag_training_sessions s ON s.plan_id = tp.id
                GROUP BY tp.id
            ),
            candidates AS (
                SELECT
                    tp.id        AS plan_id,
                    tp.name      AS plan_name,
                    p.id         AS profile_id,
                    p.age_int    AS age,
                    p.weight_kg  AS weight,
                    p.height_cm  AS height,
                    psc.session_count,
                    (abs(p.age_int - %s) * 1.0
                     + abs(COALESCE(p.weight_kg, %s) - %s) * 1.5
                     + abs(COALESCE(p.height_cm, %s) - %s) * 0.5) AS sim_score
                FROM rag_training_plans tp
                JOIN rag_user_profiles p ON p.id = tp.user_id
                JOIN plan_session_count psc ON psc.plan_id = tp.id
                WHERE p.age_int BETWEEN %s AND %s
                  AND p.weight_kg BETWEEN %s AND %s
                  AND p.height_cm BETWEEN %s AND %s
                  AND psc.session_count BETWEEN %s AND %s
            )
            SELECT * FROM candidates
            ORDER BY sim_score ASC, plan_id DESC
            LIMIT %s;
            """,
            (
                age, weight_kg, weight_kg, height_cm, height_cm,
                age_lo, age_hi, w_lo, w_hi, h_lo, h_hi,
                s_lo, s_hi,
                top_n,
            ),
        )
        return cur.fetchall() or []
    finally:
        cur.close()


def fetch_training_plan_content(db, plan_id: int) -> list[dict]:
    """All sessions + their exercises (with superset variants) for one plan."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            """
            SELECT
                s.id             AS session_id,
                s.training_name  AS session_name,
                s.training_time  AS day_hint,
                e.id             AS exercise_id,
                e.move_name      AS move1,
                e.quantity       AS qty1,
                e.move2          AS move2,
                e.quantity2      AS qty2,
                e.move3          AS move3,
                e.quantity3      AS qty3
            FROM rag_training_sessions s
            LEFT JOIN rag_training_exercises e ON e.training_id = s.id
            WHERE s.plan_id = %s
            ORDER BY s.id ASC, e.id ASC;
            """,
            (plan_id,),
        )
        rows = cur.fetchall() or []
    finally:
        cur.close()

    sessions_by_id: dict = {}
    order: list = []
    for r in rows:
        sid = r["session_id"]
        if sid not in sessions_by_id:
            sessions_by_id[sid] = {
                "session_name": _clean_html(r["session_name"]),
                "day_hint": _clean_html(r["day_hint"]),
                "exercises": [],
            }
            order.append(sid)
        if r.get("move1"):
            triplet = []
            for m, q in (
                (r.get("move1"), r.get("qty1")),
                (r.get("move2"), r.get("qty2")),
                (r.get("move3"), r.get("qty3")),
            ):
                m_clean = _clean_html(m)
                if m_clean:
                    triplet.append({"name": m_clean, "qty": _clean_html(q)})
            if triplet:
                sessions_by_id[sid]["exercises"].append(triplet)
    return [sessions_by_id[sid] for sid in order]


def format_training_plans_for_prompt(plans: list[dict], plan_contents: list[list[dict]]) -> str:
    """Compact reference text describing 3 RAG training plans for the AI prompt."""
    lines = ["═══ KOÇUN BENZER PROFİLLERE YAZDIĞI 3 GERÇEK ANTRENMAN PROGRAMI ═══"]
    for i, (plan, sessions) in enumerate(zip(plans, plan_contents), start=1):
        lines.append("")
        lines.append(
            f"── REFERANS {i} (profil: {plan['age']} yaş, "
            f"{plan['weight']} kg, {plan['height']} cm; "
            f"haftada {plan['session_count']} seans; benzerlik={plan['sim_score']:.1f}) ──"
        )
        for s in sessions:
            day = s["day_hint"] or "—"
            ex_strs = []
            for triplet in s["exercises"]:
                # Render superset as "A + B + C (qty)"
                names = " + ".join(t["name"] for t in triplet)
                qtys = " / ".join(t["qty"] for t in triplet if t["qty"])
                ex_strs.append(f"{names}" + (f" ({qtys})" if qtys else ""))
            lines.append(f"  [{day}] {s['session_name']}: " + " | ".join(ex_strs))
    lines.append("")
    lines.append("BU PROGRAMLARIN GÜN-KAS-GRUBU EŞLEŞMESİNİ VE EGZERSİZ SIRALAMASINI REFERANS AL.")
    lines.append("Öğrencinin profiline uyarla — birebir kopyalama, koç tarzında yaz.")
    return "\n".join(lines)

