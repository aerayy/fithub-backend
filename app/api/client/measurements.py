"""Body measurements CRUD endpoints."""
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from app.services.badges import check_and_award
from .routes import router


class MeasurementInput(BaseModel):
    measured_at: Optional[str] = None  # YYYY-MM-DD
    weight_kg: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    left_arm_cm: Optional[float] = None
    right_arm_cm: Optional[float] = None
    left_thigh_cm: Optional[float] = None
    right_thigh_cm: Optional[float] = None
    calves_cm: Optional[float] = None
    neck_cm: Optional[float] = None
    shoulders_cm: Optional[float] = None
    notes: Optional[str] = None


@router.post("/measurements")
def add_measurement(
    body: MeasurementInput,
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Add a new body measurement entry."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """INSERT INTO body_measurements
           (user_id, measured_at, weight_kg, chest_cm, waist_cm, hips_cm,
            left_arm_cm, right_arm_cm, left_thigh_cm, right_thigh_cm,
            calves_cm, neck_cm, shoulders_cm, notes)
           VALUES (%s, COALESCE(%s::date, CURRENT_DATE), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id, measured_at""",
        (current_user["id"], body.measured_at, body.weight_kg, body.chest_cm,
         body.waist_cm, body.hips_cm, body.left_arm_cm, body.right_arm_cm,
         body.left_thigh_cm, body.right_thigh_cm, body.calves_cm,
         body.neck_cm, body.shoulders_cm, body.notes),
    )
    row = cur.fetchone()
    db.commit()

    # Award measurement / weighin badges (fail-safe)
    newly_earned = []
    try:
        # Always trigger measurement badge
        newly_earned += check_and_award(current_user["id"], 'measurement_logged', db)
        # Also trigger weighin if weight provided
        if body.weight_kg is not None:
            newly_earned += check_and_award(current_user["id"], 'weight_logged', db)
    except Exception:
        pass

    return {
        "ok": True,
        "id": row["id"],
        "measured_at": str(row["measured_at"]),
        "newly_earned": newly_earned,
    }


@router.get("/measurements")
def get_measurements(
    limit: int = Query(30, ge=1, le=100),
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """Get measurement history, newest first."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT id, measured_at, weight_kg, chest_cm, waist_cm, hips_cm,
                  left_arm_cm, right_arm_cm, left_thigh_cm, right_thigh_cm,
                  calves_cm, neck_cm, shoulders_cm, notes, created_at
           FROM body_measurements
           WHERE user_id = %s
           ORDER BY measured_at DESC
           LIMIT %s""",
        (current_user["id"], limit),
    )
    rows = cur.fetchall()

    # Serialize dates
    for r in rows:
        r["measured_at"] = str(r["measured_at"]) if r["measured_at"] else None
        r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else None
        # Convert Decimal to float
        for key in ["weight_kg", "chest_cm", "waist_cm", "hips_cm", "left_arm_cm",
                     "right_arm_cm", "left_thigh_cm", "right_thigh_cm", "calves_cm",
                     "neck_cm", "shoulders_cm"]:
            if r.get(key) is not None:
                r[key] = float(r[key])

    return {"measurements": rows}
