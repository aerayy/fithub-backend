from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.core.security import require_role

router = APIRouter()  # ✅ prefix yok!


class CoachPackageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    duration_days: int = Field(gt=0)
    price: int = Field(ge=0)
    is_active: bool = True


class CoachPackageUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    duration_days: Optional[int] = Field(default=None, gt=0)
    price: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


@router.get("/packages")
def list_my_packages(
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT id, coach_user_id, name, description, duration_days, price, is_active, created_at, updated_at
        FROM coach_packages
        WHERE coach_user_id = %s
        ORDER BY is_active DESC, created_at DESC, id DESC
        """,
        (current_user["id"],),
    )
    return {"packages": cur.fetchall()}


@router.post("/packages")
def create_package(
    body: CoachPackageCreate,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        INSERT INTO coach_packages (coach_user_id, name, description, duration_days, price, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, coach_user_id, name, description, duration_days, price, is_active, created_at, updated_at
        """,
        (current_user["id"], body.name, body.description, body.duration_days, body.price, body.is_active),
    )
    row = cur.fetchone()
    db.commit()
    return {"package": row}


@router.put("/packages/{package_id}")
def update_package(
    package_id: int,
    body: CoachPackageUpdate,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    cur = db.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT id FROM coach_packages WHERE id=%s AND coach_user_id=%s",
        (package_id, current_user["id"]),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Package not found")

    fields = []
    values = []

    if body.name is not None:
        fields.append("name=%s")
        values.append(body.name)
    if body.description is not None:
        fields.append("description=%s")
        values.append(body.description)
    if body.duration_days is not None:
        fields.append("duration_days=%s")
        values.append(body.duration_days)
    if body.price is not None:
        fields.append("price=%s")
        values.append(body.price)
    if body.is_active is not None:
        fields.append("is_active=%s")
        values.append(body.is_active)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.extend([package_id, current_user["id"]])

    cur.execute(
        f"""
        UPDATE coach_packages
        SET {", ".join(fields)}
        WHERE id=%s AND coach_user_id=%s
        RETURNING id, coach_user_id, name, description, duration_days, price, is_active, created_at, updated_at
        """,
        tuple(values),
    )
    row = cur.fetchone()
    db.commit()
    return {"package": row}
