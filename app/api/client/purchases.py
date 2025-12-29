from fastapi import Depends
from app.core.security import require_role
from .routes import router


@router.get("/ping")
def client_ping(current_user=Depends(require_role("client"))):
    return {"ok": True, "message": "client router works"}
