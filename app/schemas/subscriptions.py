from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubscriptionConfirmRequest(BaseModel):
    coach_id: str
    plan_id: str
    subscription_ref: str


class SubscriptionConfirmResponse(BaseModel):
    ok: bool
    subscription: dict
    created: bool
