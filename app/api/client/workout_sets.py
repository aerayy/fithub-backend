"""Set bazlı antrenman kaydı: ağırlık × tekrar, egzersiz geçmişi, kişisel rekor.

Neden: uygulama yalnızca "tamamlandı" işareti tutuyordu; ilerleyici yüklenme,
egzersiz geçmişi ve rekor takibi (rakiplerin çekirdek değeri) yoktu.

- PUT /client/workout-sets            → bugünün setlerini upsert eder, rekor bilgisini döner
- GET /client/workout-sets/history    → bugün + son antrenman + en iyi + son 8 oturum

Rekor ölçütü: Epley tahmini 1RM = ağırlık × (1 + tekrar/30). Vücut ağırlığı
hareketlerinde (ağırlık 0) rekor takibi yapılmaz.
"""
import re
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field, field_validator

from app.core.database import get_db
from app.core.security import require_role
from .routes import router


class SetInput(BaseModel):
    set_index: int = Field(ge=1, le=20)
    weight_kg: Optional[float] = Field(default=None, ge=0, le=999)
    reps: Optional[int] = Field(default=None, ge=0, le=500)
    rpe: Optional[float] = Field(default=None, ge=1, le=10)


class SaveSetsInput(BaseModel):
    exercise_name: str = ""
    library_id: Optional[int] = None
    exercise_key: Optional[str] = None
    day_key: Optional[str] = None
    session_date: Optional[date] = None   # boş → bugün
    sets: List[SetInput]

    @field_validator("sets")
    @classmethod
    def _v_sets(cls, v):
        if not v:
            raise ValueError("En az bir set gönderilmeli")
        if len(v) > 20:
            raise ValueError("En fazla 20 set")
        return v


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())[:120]


def resolve_key(exercise_key: Optional[str], library_id: Optional[int], exercise_name: str) -> str:
    if exercise_key:
        return exercise_key.strip()[:160]
    if library_id:
        return f"lib:{int(library_id)}"
    n = _norm_name(exercise_name)
    if not n:
        raise HTTPException(status_code=422, detail="exercise_name veya library_id gerekli")
    return f"name:{n}"


def est_1rm(weight: Optional[float], reps: Optional[int]) -> float:
    w = float(weight or 0)
    r = int(reps or 0)
    if w <= 0 or r <= 0:
        return 0.0
    return round(w * (1 + r / 30.0), 2)


def _row_out(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "set_index": r["set_index"],
        "weight_kg": float(r["weight_kg"]) if r.get("weight_kg") is not None else None,
        "reps": r.get("reps"),
        "rpe": float(r["rpe"]) if r.get("rpe") is not None else None,
        "est_1rm": est_1rm(r.get("weight_kg"), r.get("reps")),
    }


def _best_before(cur, user_id: int, key: str, before: date) -> Optional[Dict[str, Any]]:
    cur.execute(
        """SELECT session_date, weight_kg, reps
           FROM workout_set_logs
           WHERE user_id = %s AND exercise_key = %s AND session_date < %s
             AND weight_kg IS NOT NULL AND weight_kg > 0 AND reps > 0""",
        (user_id, key, before),
    )
    best = None
    for r in cur.fetchall() or []:
        e = est_1rm(r["weight_kg"], r["reps"])
        if best is None or e > best["est_1rm"]:
            best = {"date": r["session_date"].isoformat(), "weight_kg": float(r["weight_kg"]),
                    "reps": r["reps"], "est_1rm": e}
    return best


@router.put("/workout-sets")
def save_workout_sets(
    body: SaveSetsInput,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    uid = current_user["id"]
    key = resolve_key(body.exercise_key, body.library_id, body.exercise_name)
    sdate = body.session_date or date.today()
    cur = db.cursor(cursor_factory=RealDictCursor)

    best_before = _best_before(cur, uid, key, sdate)
    saved = []
    for s in body.sets:
        cur.execute(
            """INSERT INTO workout_set_logs
               (user_id, session_date, day_key, exercise_key, exercise_name, library_id, set_index, weight_kg, reps, rpe)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (user_id, session_date, exercise_key, set_index) DO UPDATE SET
                 weight_kg = EXCLUDED.weight_kg, reps = EXCLUDED.reps, rpe = EXCLUDED.rpe,
                 exercise_name = COALESCE(EXCLUDED.exercise_name, workout_set_logs.exercise_name),
                 library_id = COALESCE(EXCLUDED.library_id, workout_set_logs.library_id),
                 day_key = COALESCE(EXCLUDED.day_key, workout_set_logs.day_key),
                 updated_at = NOW()
               RETURNING set_index, weight_kg, reps, rpe""",
            (uid, sdate, body.day_key, key, (body.exercise_name or None), body.library_id,
             s.set_index, s.weight_kg, s.reps, s.rpe),
        )
        saved.append(_row_out(cur.fetchone()))
    db.commit()

    today_best = max(saved, key=lambda x: x["est_1rm"]) if saved else None
    pr = None
    if today_best and today_best["est_1rm"] > 0 and best_before and today_best["est_1rm"] > best_before["est_1rm"]:
        pr = {"weight_kg": today_best["weight_kg"], "reps": today_best["reps"],
              "est_1rm": today_best["est_1rm"], "previous": best_before}
    return {"ok": True, "exercise_key": key, "session_date": sdate.isoformat(),
            "saved": len(saved), "sets": saved, "pr": pr, "best_before": best_before}


@router.get("/workout-sets/history")
def workout_sets_history(
    exercise_key: Optional[str] = Query(default=None),
    library_id: Optional[int] = Query(default=None),
    exercise_name: str = Query(default=""),
    limit: int = Query(default=8, ge=1, le=30),
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    uid = current_user["id"]
    key = resolve_key(exercise_key, library_id, exercise_name)
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT session_date, set_index, weight_kg, reps, rpe
           FROM workout_set_logs
           WHERE user_id = %s AND exercise_key = %s
           ORDER BY session_date DESC, set_index ASC""",
        (uid, key),
    )
    rows = cur.fetchall() or []
    by_date: Dict[str, List[Dict[str, Any]]] = {}
    order: List[str] = []
    for r in rows:
        d = r["session_date"].isoformat()
        if d not in by_date:
            by_date[d] = []
            order.append(d)
        by_date[d].append(_row_out(r))

    today = date.today().isoformat()
    sessions = []
    best = None
    for d in order:
        sets = by_date[d]
        top = max(sets, key=lambda x: x["est_1rm"]) if sets else None
        volume = round(sum((s["weight_kg"] or 0) * (s["reps"] or 0) for s in sets), 1)
        sessions.append({"date": d, "sets": sets, "top_weight_kg": top["weight_kg"] if top else None,
                         "top_reps": top["reps"] if top else None, "volume_kg": volume})
        if top and top["est_1rm"] > 0 and (best is None or top["est_1rm"] > best["est_1rm"]):
            best = {"date": d, "weight_kg": top["weight_kg"], "reps": top["reps"], "est_1rm": top["est_1rm"]}
    last = next((s for s in sessions if s["date"] != today), None)
    return {
        "exercise_key": key,
        "today": by_date.get(today, []),
        "last": last,
        "best": best,
        "sessions": sessions[:limit],
    }
