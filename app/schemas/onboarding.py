# app/schemas/onboarding.py
from pydantic import BaseModel
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

    preferred_workout_days: Optional[List[str]] = None
    preferred_workout_hours: Optional[str] = None
    nutrition_budget: Optional[str] = None
    target_weight_kg: Optional[float] = None
