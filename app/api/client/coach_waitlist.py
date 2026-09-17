# app/api/client/coach_waitlist.py — "Gerçek koçlar yakında" bekleme listesi
from typing import Optional

from fastapi import Depends
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import require_role
from .routes import router


class WaitlistIn(BaseModel):
    source: Optional[str] = Field(default=None, max_length=40)


@router.get("/coach-waitlist")
def coach_waitlist_status(db=Depends(get_db), current_user=Depends(require_role("client"))):
    cur = db.cursor()
    cur.execute("SELECT created_at FROM coach_waitlist WHERE user_id = %s", (current_user["id"],))
    row = cur.fetchone()
    return {"joined": row is not None}


@router.post("/coach-waitlist")
def coach_waitlist_join(body: WaitlistIn, db=Depends(get_db), current_user=Depends(require_role("client"))):
    """Idempotent: ikinci çağrı da joined=true döner."""
    cur = db.cursor()
    cur.execute(
        """INSERT INTO coach_waitlist (user_id, source) VALUES (%s, %s)
           ON CONFLICT (user_id) DO NOTHING""",
        (current_user["id"], (body.source or "app")[:40]),
    )
    db.commit()
    return {"joined": True}
