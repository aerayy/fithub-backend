# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str
