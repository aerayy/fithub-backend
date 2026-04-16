"""Program draft CRUD + assign — coaches can save up to 3 drafts per student."""
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from psycopg2.extras import RealDictCursor
from app.core.database import get_db
from app.core.security import require_role
from .routes import router

MAX_DRAFTS = 3


class DraftInput(BaseModel):
    name: Optional[str] = 'Taslak'
    payload: dict = {}


class DraftUpdateInput(BaseModel):
    name: Optional[str] = None
    payload: Optional[dict] = None


def _verify_coach_student(cur, coach_id: int, student_id: int):
    cur.execute(
        "SELECT 1 FROM clients WHERE user_id=%s AND assigned_coach_id=%s",
        (student_id, coach_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=403, detail="Bu öğrenci size atanmamış")


def _enforce_max(cur, table: str, coach_id: int, student_id: int):
    """Keep max 3 drafts per coach+student. Delete oldest if over limit."""
    cur.execute(
        f"""
        DELETE FROM {table}
        WHERE id IN (
            SELECT id FROM {table}
            WHERE coach_user_id = %s AND client_user_id = %s
            ORDER BY created_at DESC
            OFFSET %s
        )
        """,
        (coach_id, student_id, MAX_DRAFTS),
    )


def _serialize(row):
    r = dict(row)
    for key in ('created_at', 'updated_at'):
        if r.get(key) and hasattr(r[key], 'isoformat'):
            r[key] = r[key].isoformat()
    return r


# ──────────────────── WORKOUT DRAFTS ────────────────────

@router.get("/students/{student_id}/workout-drafts")
def list_workout_drafts(
    student_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_coach_student(cur, coach_id, student_id)
    cur.execute(
        """SELECT id, name, payload, created_at, updated_at
           FROM workout_program_drafts
           WHERE coach_user_id = %s AND client_user_id = %s
           ORDER BY created_at DESC""",
        (coach_id, student_id),
    )
    return {"drafts": [_serialize(r) for r in cur.fetchall()]}


@router.post("/students/{student_id}/workout-drafts")
def create_workout_draft(
    student_id: int,
    body: DraftInput,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_coach_student(cur, coach_id, student_id)

    from psycopg2.extras import Json
    cur.execute(
        """INSERT INTO workout_program_drafts (coach_user_id, client_user_id, name, payload)
           VALUES (%s, %s, %s, %s) RETURNING id, name, created_at""",
        (coach_id, student_id, body.name or 'Taslak', Json(body.payload)),
    )
    row = cur.fetchone()

    _enforce_max(cur, 'workout_program_drafts', coach_id, student_id)
    db.commit()
    return {"ok": True, "draft": _serialize(row)}


@router.put("/students/{student_id}/workout-drafts/{draft_id}")
def update_workout_draft(
    student_id: int,
    draft_id: int,
    body: DraftUpdateInput,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_coach_student(cur, coach_id, student_id)

    fields = []
    values = []
    if body.name is not None:
        fields.append("name = %s")
        values.append(body.name)
    if body.payload is not None:
        from psycopg2.extras import Json
        fields.append("payload = %s")
        values.append(Json(body.payload))
    if not fields:
        raise HTTPException(status_code=400, detail="Güncellenecek alan belirtilmedi")

    fields.append("updated_at = NOW()")
    values.extend([draft_id, coach_id, student_id])

    cur.execute(
        f"""UPDATE workout_program_drafts
            SET {', '.join(fields)}
            WHERE id = %s AND coach_user_id = %s AND client_user_id = %s
            RETURNING id, name, payload, created_at, updated_at""",
        values,
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Taslak bulunamadı")
    db.commit()
    return {"ok": True, "draft": _serialize(row)}


@router.delete("/students/{student_id}/workout-drafts/{draft_id}")
def delete_workout_draft(
    student_id: int,
    draft_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """DELETE FROM workout_program_drafts
           WHERE id = %s AND coach_user_id = %s AND client_user_id = %s
           RETURNING id""",
        (draft_id, coach_id, student_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Taslak bulunamadı")
    db.commit()
    return {"ok": True}


@router.post("/students/{student_id}/workout-drafts/{draft_id}/assign")
def assign_workout_draft(
    student_id: int,
    draft_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Activate a draft as the student's current workout program."""
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_coach_student(cur, coach_id, student_id)

    cur.execute(
        "SELECT payload, name FROM workout_program_drafts WHERE id = %s AND coach_user_id = %s AND client_user_id = %s",
        (draft_id, coach_id, student_id),
    )
    draft = cur.fetchone()
    if not draft:
        raise HTTPException(status_code=404, detail="Taslak bulunamadı")

    payload = draft["payload"]
    draft_name = draft["name"]

    # Deactivate current active programs
    cur.execute(
        "UPDATE workout_programs SET is_active = FALSE WHERE client_user_id = %s AND is_active = TRUE",
        (student_id,),
    )

    # Insert as active program
    from psycopg2.extras import Json
    cur.execute(
        """INSERT INTO workout_programs (client_user_id, coach_user_id, program_name, day_payload, is_active, created_at)
           VALUES (%s, %s, %s, %s, TRUE, NOW()) RETURNING id""",
        (student_id, coach_id, draft_name, Json(payload)),
    )
    program_id = cur.fetchone()["id"]

    # Update subscription
    cur.execute(
        """UPDATE subscriptions SET program_state = 'assigned', program_assigned_at = NOW()
           WHERE client_user_id = %s AND coach_user_id = %s AND status = 'active'""",
        (student_id, coach_id),
    )

    db.commit()
    return {"ok": True, "program_id": program_id, "draft_name": draft_name}


# ──────────────────── NUTRITION DRAFTS ────────────────────

@router.get("/students/{student_id}/nutrition-drafts")
def list_nutrition_drafts(
    student_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_coach_student(cur, coach_id, student_id)
    cur.execute(
        """SELECT id, name, payload, created_at, updated_at
           FROM nutrition_program_drafts
           WHERE coach_user_id = %s AND client_user_id = %s
           ORDER BY created_at DESC""",
        (coach_id, student_id),
    )
    return {"drafts": [_serialize(r) for r in cur.fetchall()]}


@router.post("/students/{student_id}/nutrition-drafts")
def create_nutrition_draft(
    student_id: int,
    body: DraftInput,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_coach_student(cur, coach_id, student_id)

    from psycopg2.extras import Json
    cur.execute(
        """INSERT INTO nutrition_program_drafts (coach_user_id, client_user_id, name, payload)
           VALUES (%s, %s, %s, %s) RETURNING id, name, created_at""",
        (coach_id, student_id, body.name or 'Taslak', Json(body.payload)),
    )
    row = cur.fetchone()

    _enforce_max(cur, 'nutrition_program_drafts', coach_id, student_id)
    db.commit()
    return {"ok": True, "draft": _serialize(row)}


@router.put("/students/{student_id}/nutrition-drafts/{draft_id}")
def update_nutrition_draft(
    student_id: int,
    draft_id: int,
    body: DraftUpdateInput,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_coach_student(cur, coach_id, student_id)

    fields = []
    values = []
    if body.name is not None:
        fields.append("name = %s")
        values.append(body.name)
    if body.payload is not None:
        from psycopg2.extras import Json
        fields.append("payload = %s")
        values.append(Json(body.payload))
    if not fields:
        raise HTTPException(status_code=400, detail="Güncellenecek alan belirtilmedi")

    fields.append("updated_at = NOW()")
    values.extend([draft_id, coach_id, student_id])

    cur.execute(
        f"""UPDATE nutrition_program_drafts
            SET {', '.join(fields)}
            WHERE id = %s AND coach_user_id = %s AND client_user_id = %s
            RETURNING id, name, payload, created_at, updated_at""",
        values,
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Taslak bulunamadı")
    db.commit()
    return {"ok": True, "draft": _serialize(row)}


@router.delete("/students/{student_id}/nutrition-drafts/{draft_id}")
def delete_nutrition_draft(
    student_id: int,
    draft_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """DELETE FROM nutrition_program_drafts
           WHERE id = %s AND coach_user_id = %s AND client_user_id = %s
           RETURNING id""",
        (draft_id, coach_id, student_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Taslak bulunamadı")
    db.commit()
    return {"ok": True}


@router.post("/students/{student_id}/nutrition-drafts/{draft_id}/assign")
def assign_nutrition_draft(
    student_id: int,
    draft_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    """Activate a draft as the student's current nutrition program."""
    coach_id = current_user["id"]
    cur = db.cursor(cursor_factory=RealDictCursor)
    _verify_coach_student(cur, coach_id, student_id)

    cur.execute(
        "SELECT payload, name FROM nutrition_program_drafts WHERE id = %s AND coach_user_id = %s AND client_user_id = %s",
        (draft_id, coach_id, student_id),
    )
    draft = cur.fetchone()
    if not draft:
        raise HTTPException(status_code=404, detail="Taslak bulunamadı")

    payload = draft["payload"]
    draft_name = draft["name"]

    # Deactivate current
    cur.execute(
        "UPDATE nutrition_programs SET is_active = FALSE WHERE client_user_id = %s AND is_active = TRUE",
        (student_id,),
    )

    # Insert as active
    from psycopg2.extras import Json
    cur.execute(
        """INSERT INTO nutrition_programs (client_user_id, coach_user_id, program_name, plan_payload, is_active, created_at)
           VALUES (%s, %s, %s, %s, TRUE, NOW()) RETURNING id""",
        (student_id, coach_id, draft_name, Json(payload)),
    )
    program_id = cur.fetchone()["id"]

    # Update subscription
    cur.execute(
        """UPDATE subscriptions SET program_state = 'assigned', program_assigned_at = NOW()
           WHERE client_user_id = %s AND coach_user_id = %s AND status = 'active'""",
        (student_id, coach_id),
    )

    db.commit()
    return {"ok": True, "program_id": program_id, "draft_name": draft_name}
