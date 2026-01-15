from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


def validate_services(services: Optional[List[str]]) -> List[str]:
    """
    Validate and normalize services list.
    - If None, return empty list
    - Max 12 tags
    - Each tag max 40 chars, trimmed
    """
    if services is None:
        return []
    
    # Trim and filter empty strings
    normalized = [s.strip() for s in services if s and s.strip()]
    
    # Max 12 tags
    if len(normalized) > 12:
        raise ValueError("Maximum 12 service tags allowed")
    
    # Each tag max 40 chars
    for tag in normalized:
        if len(tag) > 40:
            raise ValueError(f"Service tag '{tag}' exceeds 40 characters")
    
    return normalized


class CoachPackageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    duration_days: int = Field(gt=0)
    price: int = Field(ge=0)  # TL integer
    is_active: bool = True
    services: Optional[List[str]] = Field(default=None, description="List of service tags (max 12, each max 40 chars)")
    
    @field_validator('services')
    @classmethod
    def validate_services_field(cls, v):
        return validate_services(v)


class CoachPackageUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    duration_days: Optional[int] = Field(default=None, gt=0)
    price: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    services: Optional[List[str]] = Field(default=None, description="List of service tags (max 12, each max 40 chars)")
    
    @field_validator('services')
    @classmethod
    def validate_services_field(cls, v):
        return validate_services(v)