from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from pydantic import BaseModel
from typing import List, Optional

from app.core.security import require_role

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


# ---- Schemas ----
class MealIn(BaseModel):
    meal_type: str  # breakfast/lunch/dinner/snack...
    content: Optional[str] = None  # şimdilik text
    order_index: int = 0
    planned_time: Optional[str] = None  # "09:30" (HH:MM)


class NutritionProgramCreate(BaseModel):
    client_user_id: int
    coach_user_id: int
    title: str = "Nutrition Program"
    meals: List[MealIn] = []


# ---- Helpers ----
def fetch_active_nutrition_program(client_user_id: int, db):
    cur = db.cursor()

    cur.execute(
        """
        SELECT id, client_user_id, coach_user_id, title, is_active, created_at, updated_at
        FROM nutrition_programs
        WHERE client_user_id = %s AND is_active = TRUE
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (client_user_id,),
    )
    program = cur.fetchone()
    if not program:
        return None

    program_id = program["id"]

    cur.execute(
        """
        SELECT id, meal_type, content, order_index, planned_time
        FROM nutrition_meals
        WHERE nutrition_program_id = %s
        ORDER BY planned_time NULLS LAST, order_index ASC, id ASC
        """,
        (program_id,),
    )
    meals = cur.fetchall() or []

    # Normalize planned_time to "HH:MM" for response (Postgres TIME -> str)
    for meal in meals:
        pt = meal.get("planned_time")
        if pt is not None:
            meal["planned_time"] = pt.strftime("%H:%M") if hasattr(pt, "strftime") else str(pt)

    program["meals"] = meals
    return program


# ---- Endpoints ----
@router.get("/active/{client_user_id}")
def get_active_nutrition(
    client_user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_role("client", "coach")),
):
    # client sadece kendi programını görebilsin
    if current_user["role"] == "client" and current_user["id"] != client_user_id:
        raise HTTPException(status_code=403, detail="You can only access your own nutrition program")

    program = fetch_active_nutrition_program(client_user_id, db)
    if not program:
        raise HTTPException(status_code=404, detail="Active nutrition program not found")

    return {"program": program}


@router.post("/set-active")
def set_active_nutrition(
    payload: NutritionProgramCreate,
    db=Depends(get_db),
    current_user=Depends(require_role("coach")),
):
    # Token'daki koç id'si ile payload'daki aynı olmalı
    if current_user["id"] != payload.coach_user_id:
        raise HTTPException(status_code=403, detail="coach_user_id mismatch")

    cur = db.cursor()

    try:
        # 1) mevcut aktifi pasifle
        cur.execute(
            """
            UPDATE nutrition_programs
            SET is_active = FALSE, updated_at = NOW()
            WHERE client_user_id = %s AND is_active = TRUE
            """,
            (payload.client_user_id,),
        )

        # 2) yeni programı ekle
        cur.execute(
            """
            INSERT INTO nutrition_programs (client_user_id, coach_user_id, title, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, TRUE, NOW(), NOW())
            RETURNING id, client_user_id, coach_user_id, title, is_active, created_at, updated_at
            """,
            (payload.client_user_id, payload.coach_user_id, payload.title),
        )
        program = cur.fetchone()
        program_id = program["id"]

        # 3) meals ekle (planned_time: TIME, "HH:MM" string; None allowed)
        for meal in payload.meals:
            cur.execute(
                """
                INSERT INTO nutrition_meals (nutrition_program_id, meal_type, content, order_index, planned_time, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """,
                (program_id, meal.meal_type, meal.content, meal.order_index, meal.planned_time),
            )

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    program = fetch_active_nutrition_program(payload.client_user_id, db)
    return {"program": program}
