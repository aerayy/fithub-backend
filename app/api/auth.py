# app/api/auth.py
import logging
from fastapi import APIRouter, HTTPException, Depends
import bcrypt
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import get_db
from app.core.security import create_token
from app.schemas.auth import SignUpRequest, LoginRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup(req: SignUpRequest, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()

    # ✅ Flutter client app: role backend tarafından otomatik "client"
    role = "client"

    cur.execute(
        """
        INSERT INTO users (email, password_hash, full_name, timezone, phone_number, role, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        RETURNING id, email, full_name, role
        """,
        (req.email, hashed, None, "Europe/Istanbul", req.phone, role),
    )

    user = cur.fetchone()
    user_id = user["id"]
    
    # Insert into clients table for client role users
    # Using ON CONFLICT DO NOTHING for idempotency (if row already exists, skip)
    cur.execute(
        """
        INSERT INTO clients (user_id, onboarding_done)
        VALUES (%s, false)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )
    
    if cur.rowcount > 0:
        logger.debug(f"Created clients row for user_id={user_id} during signup")
    else:
        logger.debug(f"clients row already exists for user_id={user_id}, skipped insert")
    
    db.commit()

    token = create_token(user["id"])
    return {"token": token, "user": user}



@router.post("/login")
def login(req: LoginRequest, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        """
        SELECT id, email, full_name, password_hash
        FROM users
        WHERE email = %s
        """,
        (req.email,),
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user["id"])
    return {"token": token, "user_id": user["id"], "user_email": user["email"]}

@router.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """
    Swagger OAuth2PasswordBearer için standart endpoint.
    form_data.username = email
    form_data.password = password
    """
    cur = db.cursor()
    cur.execute(
        """
        SELECT id, email, full_name, password_hash
        FROM users
        WHERE email = %s
        """,
        (form_data.username,),
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(form_data.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_token(user["id"])
    return {"access_token": access_token, "token_type": "bearer"}

