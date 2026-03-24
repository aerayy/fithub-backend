"""Coach transformation gallery CRUD."""
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from .routes import router


class TransformationInput(BaseModel):
    before_image_url: str
    after_image_url: str
    student_name: Optional[str] = "Anonim"
    weight_lost_kg: Optional[float] = None
    duration_weeks: Optional[int] = None
    description: Optional[str] = None


@router.get("/transformations")
def get_my_transformations(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Get coach's own transformations."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """SELECT id, before_image_url, after_image_url, student_name,
                  weight_lost_kg, duration_weeks, description, is_active, created_at
           FROM coach_transformations
           WHERE coach_user_id = %s ORDER BY created_at DESC""",
        (current_user["id"],),
    )
    rows = cur.fetchall()
    for r in rows:
        if r.get("weight_lost_kg") is not None:
            r["weight_lost_kg"] = float(r["weight_lost_kg"])
        r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else None
    return {"transformations": rows}


@router.post("/transformations")
def add_transformation(
    body: TransformationInput,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Add a new transformation."""
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """INSERT INTO coach_transformations
           (coach_user_id, before_image_url, after_image_url, student_name, weight_lost_kg, duration_weeks, description)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (current_user["id"], body.before_image_url, body.after_image_url,
         body.student_name, body.weight_lost_kg, body.duration_weeks, body.description),
    )
    row = cur.fetchone()
    db.commit()
    return {"ok": True, "id": row["id"]}


@router.delete("/transformations/{transformation_id}")
def delete_transformation(
    transformation_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Delete a transformation."""
    cur = db.cursor()
    cur.execute(
        "DELETE FROM coach_transformations WHERE id = %s AND coach_user_id = %s",
        (transformation_id, current_user["id"]),
    )
    db.commit()
    return {"ok": True}
