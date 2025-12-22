from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
import psycopg2
from psycopg2.extras import RealDictCursor, Json

# === CONFIG ===
JWT_SECRET = "CHANGE_THIS_TO_A_RANDOM_SECRET"
JWT_ALGORITHM = "HS256"

DB_NAME = "fithub"
DB_USER = "postgres"
DB_PASSWORD = "Eray123!"   # BURAYI DEĞİŞTİR
DB_HOST = "localhost"
DB_PORT = 5433

app = FastAPI()

# CORS – geliştirme için herkese açık
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # istersen daha sonra kısıtlarsın
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === DB CONNECTION ===
def get_db():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        cursor_factory=RealDictCursor,
    )
    try:
        yield conn
    finally:
        conn.close()

# === MODELLER ===
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


from typing import Optional, List

class OnboardingRequest(BaseModel):
    user_id: int

    full_name: Optional[str] = None

    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[int] = None

    gender: Optional[str] = None
    your_goal: Optional[str] = None
    body_type: Optional[str] = None
    experience: Optional[str] = None
    how_fit: Optional[str] = None
    knee_pain: Optional[str] = None
    pushups: Optional[str] = None
    stressed: Optional[str] = None
    commit: Optional[str] = None
    pref_workout_length: Optional[str] = None
    how_motivated: Optional[str] = None
    plan_reference: Optional[str] = None

    body_part_focus: Optional[List[str]] = None
    bad_habit: Optional[List[str]] = None
    what_motivate: Optional[List[str]] = None
    workout_place: Optional[List[str]] = None





    
# === JWT ===
def create_token(user_id: int):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# === ENDPOINTLER ===
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/signup")
def signup(req: SignUpRequest, db=Depends(get_db)):
    print("SIGNUP CALLED FOR:", req.email)
    cur = db.cursor()

    # Email kontrolü
    cur.execute("SELECT id FROM users WHERE email = %s", (req.email,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Şifre hashle
    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()

    # Kullanıcıyı ekle
    cur.execute("""
        INSERT INTO users (email, password_hash, full_name, timezone, phone_number, role, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        RETURNING id, email, full_name
    """, (
        req.email,
        hashed,
        None,               # full_name onboarding'de alınacak
        "Europe/Istanbul",  # sabit
        req.phone,          # phone → phone_number
        "client"            # varsayılan rol
    ))

    user = cur.fetchone()
    print("INSERTED USER:", user)
    db.commit()

    token = create_token(user["id"])

    return {
        "token": token,
        "user": user
    }


@app.post("/auth/login")
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
    return {
    "token": token,
    "user_id": user["id"],
    "user_email": user["email"],
}


@app.post("/client/onboarding")
def save_onboarding(req: OnboardingRequest, db=Depends(get_db)):
    # DEBUG 1: FastAPI'ye gerçekten ne geliyor?
    print("=== RAW ONBOARDING REQUEST ===")
    print(req.dict())
    print("FIELDS:", list(req.dict().keys()))
    print("================================")

    cur = db.cursor()

    cur.execute(
        """
        INSERT INTO client_onboarding (
            user_id,
            full_name,
            age,
            weight_kg,
            height_cm,
            gender,
            your_goal,
            body_type,
            experience,
            how_fit,
            knee_pain,
            pushups,
            stressed,
            commit,
            pref_workout_length,
            how_motivated,
            plan_reference,
            body_part_focus,
            bad_habit,
            what_motivate,
            workout_place,
            created_at,
            updated_at
        )
        VALUES (
            %(user_id)s,
            %(full_name)s,
            %(age)s,
            %(weight_kg)s,
            %(height_cm)s,
            %(gender)s,
            %(your_goal)s,
            %(body_type)s,
            %(experience)s,
            %(how_fit)s,
            %(knee_pain)s,
            %(pushups)s,
            %(stressed)s,
            %(commit)s,
            %(pref_workout_length)s,
            %(how_motivated)s,
            %(plan_reference)s,
            %(body_part_focus)s,
            %(bad_habit)s,
            %(what_motivate)s,
            %(workout_place)s,
            NOW(),
            NOW()
        )
        ON CONFLICT (user_id) DO UPDATE SET
            full_name          = EXCLUDED.full_name,
            age                = EXCLUDED.age,
            weight_kg          = EXCLUDED.weight_kg,
            height_cm          = EXCLUDED.height_cm,
            gender             = EXCLUDED.gender,
            your_goal          = EXCLUDED.your_goal,
            body_type          = EXCLUDED.body_type,
            experience         = EXCLUDED.experience,
            how_fit            = EXCLUDED.how_fit,
            knee_pain          = EXCLUDED.knee_pain,
            pushups            = EXCLUDED.pushups,
            stressed           = EXCLUDED.stressed,
            commit             = EXCLUDED.commit,
            pref_workout_length= EXCLUDED.pref_workout_length,
            how_motivated      = EXCLUDED.how_motivated,
            plan_reference     = EXCLUDED.plan_reference,
            body_part_focus    = EXCLUDED.body_part_focus,
            bad_habit          = EXCLUDED.bad_habit,
            what_motivate      = EXCLUDED.what_motivate,
            workout_place      = EXCLUDED.workout_place,
            updated_at         = NOW()
        RETURNING
            id,
            user_id,
            full_name,
            age,
            weight_kg,
            height_cm,
            your_goal,
            experience,
            body_part_focus,
            bad_habit,
            what_motivate,
            workout_place;
        """,
        {
            "user_id": req.user_id,
            "full_name": req.full_name,
            "age": req.age,
            "weight_kg": req.weight_kg,
            "height_cm": req.height_cm,
            "gender": req.gender,
            "your_goal": req.your_goal,
            "body_type": req.body_type,
            "experience": req.experience,
            "how_fit": req.how_fit,
            "knee_pain": req.knee_pain,
            "pushups": req.pushups,
            "stressed": req.stressed,
            "commit": req.commit,
            "pref_workout_length": req.pref_workout_length,
            "how_motivated": req.how_motivated,
            "plan_reference": req.plan_reference,
            "body_part_focus": Json(req.body_part_focus) if req.body_part_focus is not None else None,
            "bad_habit": Json(req.bad_habit) if req.bad_habit is not None else None,
            "what_motivate": Json(req.what_motivate) if req.what_motivate is not None else None,
            "workout_place": Json(req.workout_place) if req.workout_place is not None else None,
        },
    )

    profile = cur.fetchone()
    # DEBUG 2: DB'ye ne yazdık / güncelledik?
    print("=== SAVED ONBOARDING ROW ===")
    print(profile)
    print("================================")

    db.commit()

    return {"profile": profile}

@app.get("/client/onboarding/{user_id}")
def get_onboarding(user_id: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        """
        SELECT
            id,
            user_id,
            full_name,
            age,
            gender,
            weight_kg,
            height_cm,
            gender,
            your_goal,
            body_type,
            experience,
            how_fit,
            knee_pain,
            pushups,
            stressed,
            commit,
            pref_workout_length,
            how_motivated,
            plan_reference,
            body_part_focus,
            bad_habit,
            what_motivate,
            workout_place
        FROM client_onboarding
        WHERE user_id = %s
        """,
        (user_id,),
    )
    profile = cur.fetchone()
    if not profile:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    return {"profile": profile}
