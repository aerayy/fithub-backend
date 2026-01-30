"""
Client endpoint: get own active nutrition program without providing id.
GET /client/nutrition/active
"""
from fastapi import Depends, HTTPException
from app.core.database import get_db
from app.core.security import require_role
from app.api.nutrition import fetch_active_nutrition_program
from .routes import router


@router.get("/nutrition/active")
def client_get_active_nutrition(
    db=Depends(get_db),
    current_user=Depends(require_role("client")),
):
    """
    Client fetches their own active nutrition program (no id in path).
    Returns 404 if no active program.
    """
    client_user_id = current_user["id"]
    program = fetch_active_nutrition_program(client_user_id, db)
    if not program:
        raise HTTPException(status_code=404, detail="Active nutrition program not found")
    return {"program": program}
