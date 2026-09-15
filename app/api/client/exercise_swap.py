"""Egzersiz değiştirme: alternatif öneri + programda yer değiştirme.

- GET  /client/exercise-alternatives?library_id=..&limit=6[&equipment=bodyweight,dumbbell]
  Aynı hareket kalıbı (movement_pattern) + örtüşen birincil kas; aynı ekipman ve
  görseli olanlar önce, karmaşıklık yakınlığına göre sıralı.
- POST /client/workout-exercises/swap
  Aktif programda (varsayılan: tüm haftalarda) verilen gündeki egzersizi yenisiyle
  değiştirir: workout_exercises satırı + workout_days.day_payload öğesi. Koça
  activity_log ile bildirilir.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Query
from psycopg2.extras import Json, RealDictCursor
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import require_role
from .routes import router

logger = logging.getLogger(__name__)

_EX_COLS = "id, canonical_name, movement_pattern, equipment_type, equipment_class, primary_muscles, secondary_muscles, complexity, level, gif_url"


def _ex_out(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "library_id": r["id"],
        "name": r["canonical_name"],
        "movement_pattern": r.get("movement_pattern"),
        "equipment_type": r.get("equipment_type"),
        "primary_muscles": list(r.get("primary_muscles") or []),
        "complexity": r.get("complexity"),
        "level": r.get("level"),
        "gif_url": r.get("gif_url"),
    }


@router.get("/exercise-alternatives")
def exercise_alternatives(
    library_id: int = Query(..., ge=1),
    limit: int = Query(6, ge=1, le=20),
    equipment: Optional[str] = Query(default=None, description="virgülle: bodyweight,dumbbell,..."),
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(f"SELECT {_EX_COLS} FROM exercise_library WHERE id = %s", (library_id,))
    src = cur.fetchone()
    if not src:
        raise HTTPException(status_code=404, detail="Egzersiz bulunamadı")
    muscles = list(src.get("primary_muscles") or [])
    eq_filter = [e.strip().lower() for e in (equipment or "").split(",") if e.strip()]

    sql = f"""SELECT {_EX_COLS}
              FROM exercise_library
              WHERE id <> %s AND movement_pattern = %s"""
    params: List[Any] = [library_id, src.get("movement_pattern")]
    if muscles:
        sql += " AND primary_muscles && %s"
        params.append(muscles)
    if eq_filter:
        sql += " AND lower(equipment_type) = ANY(%s)"
        params.append(eq_filter)
    sql += """
              ORDER BY (equipment_type = %s) DESC, (gif_url IS NOT NULL) DESC,
                       ABS(COALESCE(complexity, 2) - %s) ASC, canonical_name ASC
              LIMIT %s"""
    params.extend([src.get("equipment_type"), int(src.get("complexity") or 2), limit])
    cur.execute(sql, tuple(params))
    alts = [_ex_out(r) for r in (cur.fetchall() or [])]
    return {"source": _ex_out(src), "alternatives": alts, "count": len(alts)}


class SwapInput(BaseModel):
    day_key: str = Field(min_length=3, max_length=3)         # mon..sun
    new_library_id: int = Field(ge=1)
    old_library_id: Optional[int] = None
    old_name: Optional[str] = None
    week_index: Optional[int] = None
    all_weeks: bool = True


def _replace_in_payload(payload: Any, old_id: Optional[int], old_name: str, new: Dict[str, Any]) -> int:
    """day_payload.blocks[].items[] içinde eşleşen öğeleri yenisiyle değiştirir; sayı döner."""
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            return 0
    if not isinstance(payload, dict):
        return 0
    n = 0
    for block in payload.get("blocks", []) or []:
        for item in block.get("items", []) or []:
            if not isinstance(item, dict):
                continue
            item_id = item.get("library_id")
            try:
                item_id = int(item_id) if item_id is not None else None
            except Exception:
                item_id = None
            same = (old_id is not None and item_id == old_id) or \
                   (old_name and (item.get("name") or "").strip().lower() == old_name)
            if same:
                item["name"] = new["canonical_name"]
                item["library_id"] = new["id"]
                if new.get("gif_url"):
                    item["gif_url"] = new["gif_url"]
                item["swapped"] = True
                n += 1
    return n if n == 0 else n, payload


@router.post("/workout-exercises/swap")
def swap_workout_exercise(
    body: SwapInput,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    uid = current_user["id"]
    if body.old_library_id is None and not (body.old_name or "").strip():
        raise HTTPException(status_code=422, detail="old_library_id veya old_name gerekli")
    old_name = (body.old_name or "").strip().lower()
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(f"SELECT {_EX_COLS} FROM exercise_library WHERE id = %s", (body.new_library_id,))
    new = cur.fetchone()
    if not new:
        raise HTTPException(status_code=404, detail="Yeni egzersiz bulunamadı")

    cur.execute(
        """SELECT id, coach_user_id FROM workout_programs
           WHERE client_user_id = %s AND is_active = TRUE
           ORDER BY updated_at DESC NULLS LAST, id DESC LIMIT 1""",
        (uid,),
    )
    prog = cur.fetchone()
    if not prog:
        raise HTTPException(status_code=404, detail="Aktif antrenman programı yok")

    sql = "SELECT id, week_index, day_payload FROM workout_days WHERE workout_program_id = %s AND day_of_week = %s"
    params: List[Any] = [prog["id"], body.day_key]
    if not body.all_weeks and body.week_index is not None:
        sql += " AND week_index = %s"
        params.append(body.week_index)
    cur.execute(sql + " ORDER BY week_index, id", tuple(params))
    days = cur.fetchall() or []
    if not days:
        raise HTTPException(status_code=404, detail="Gün bulunamadı")

    replaced_rows = 0
    replaced_days = 0
    for d in days:
        cur.execute(
            """UPDATE workout_exercises
               SET exercise_name = %s, exercise_library_id = %s, updated_at = NOW()
               WHERE workout_day_id = %s
                 AND ((%s::int IS NOT NULL AND exercise_library_id = %s) OR lower(exercise_name) = %s)""",
            (new["canonical_name"], new["id"], d["id"], body.old_library_id, body.old_library_id, old_name),
        )
        replaced_rows += cur.rowcount or 0
        res = _replace_in_payload(d.get("day_payload"), body.old_library_id, old_name, new)
        if isinstance(res, tuple):
            n, payload = res
            if n:
                cur.execute("UPDATE workout_days SET day_payload = %s, updated_at = NOW() WHERE id = %s",
                            (Json(payload), d["id"]))
                replaced_days += 1
    if replaced_rows == 0 and replaced_days == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="Değiştirilecek egzersiz bu günde bulunamadı")
    db.commit()

    try:
        from app.services.activity_log import log_activity
        log_activity(
            client_user_id=uid, coach_user_id=prog.get("coach_user_id"), action_type="exercise_swapped",
            title=f"{(body.old_name or ('#%s' % body.old_library_id))} → {new['canonical_name']} ({body.day_key})",
        )
    except Exception:
        pass

    return {"ok": True, "replaced_days": replaced_days, "replaced_rows": replaced_rows, "exercise": _ex_out(new)}
