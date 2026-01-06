# app/schemas/admin.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class CreateCoachRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    price_per_month: Optional[float] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    rating_count: Optional[int] = Field(None, ge=0)
    specialties: Optional[List[str]] = None
    instagram: Optional[str] = None
    is_active: Optional[bool] = True

    class Config:
        json_schema_extra = {
            "example": {
                "email": "coach@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
                "bio": "Experienced fitness coach with 10+ years",
                "photo_url": "https://example.com/photo.jpg",
                "price_per_month": 99.99,
                "rating": 4.5,
                "rating_count": 10,
                "specialties": ["Weight Loss", "Strength Training", "Nutrition"],
                "instagram": "@johndoe",
                "is_active": True
            }
        }
