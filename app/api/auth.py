# app/api/auth.py
import logging
from fastapi import APIRouter, HTTPException, Depends
import bcrypt
from fastapi.security import OAuth2PasswordRequestForm
import psycopg2

from app.core.database import get_db
from app.core.security import create_token
from app.schemas.auth import SignUpRequest, LoginRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup(req: SignUpRequest, db=Depends(get_db)):
    cur = db.cursor()
    
    # Store original autocommit setting
    original_autocommit = db.autocommit
    
    try:
        # Ensure we're in transaction mode
        db.autocommit = False
        
        cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()

        # ✅ Flutter client app: role backend tarafından otomatik "client"
        role = "client"

        print(f"[SIGNUP] Creating user with email={req.email}, role={role}")
        
        cur.execute(
            """
            INSERT INTO users (email, password_hash, full_name, timezone, phone_number, role, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id, email, full_name, role
            """,
            (req.email, hashed, None, "Europe/Istanbul", req.phone, role),
        )

        user = cur.fetchone()
        if not user:
            db.rollback()
            print(f"[SIGNUP] ERROR: User insert returned no row!")
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        user_id = user["id"]
        user_role = user["role"]
        
        print(f"[SIGNUP] User created successfully: user_id={user_id}, role={user_role}")

        # Insert into clients table only if role is 'client'
        if user_role == "client":
            print(f"[SIGNUP] Role is 'client', inserting into clients table for user_id={user_id}")
            cur.execute(
                """
                INSERT INTO clients (user_id, onboarding_done)
                VALUES (%s, FALSE)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (user_id,),
            )
            
            rows_affected = cur.rowcount
            if rows_affected > 0:
                print(f"[SIGNUP] Successfully inserted clients row for user_id={user_id}, rows_affected={rows_affected}")
            else:
                print(f"[SIGNUP] clients row already exists for user_id={user_id} (ON CONFLICT), rows_affected={rows_affected}")
        else:
            print(f"[SIGNUP] Role is '{user_role}', skipping clients table insert")

        # Commit both inserts (users + clients if applicable)
        print(f"[SIGNUP] Committing transaction...")
        db.commit()
        print(f"[SIGNUP] Transaction committed successfully")

        token = create_token(user["id"])
        return {"token": token, "user": user}
        
    except HTTPException:
        # Re-raise HTTP exceptions after rollback
        db.rollback()
        print(f"[SIGNUP] HTTPException raised, rolled back transaction")
        raise
    except psycopg2.Error as e:
        # Database errors
        db.rollback()
        print(f"[SIGNUP] Database error: {type(e).__name__}: {e}")
        print(f"[SIGNUP] Rolled back transaction due to database error")
        raise HTTPException(status_code=500, detail=f"Database error during signup: {str(e)}")
    except Exception as e:
        # Any other unexpected errors
        db.rollback()
        print(f"[SIGNUP] Unexpected error: {type(e).__name__}: {e}")
        print(f"[SIGNUP] Rolled back transaction due to unexpected error")
        raise HTTPException(status_code=500, detail=f"Unexpected error during signup: {str(e)}")
    finally:
        # Restore original autocommit setting
        db.autocommit = original_autocommit



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

