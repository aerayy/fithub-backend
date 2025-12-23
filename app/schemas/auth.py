# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional

from pydantic import BaseModel
from typing import Optional, Literal

class SignUpRequest(BaseModel):
    email: str
    password: str
    phone: Optional[str] = None
    role: Literal["client", "coach"] = "client"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
