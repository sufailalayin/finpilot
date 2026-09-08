from datetime import datetime
from pydantic import BaseModel, Field


class SubscriptionStatusResponse(BaseModel):
    plan_code: str
    status: str
    trial_ends_at: datetime | None
    paid_until: datetime | None
    provider: str | None


class GooglePlayVerifyRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=200)
    purchase_token: str = Field(min_length=1, max_length=1000)


class GooglePlayVerifyResponse(BaseModel):
    verified: bool
    plan_code: str
    status: str
    paid_until: datetime | None



class FeatureAccess(BaseModel):
    code: str
    name: str
    included: bool
    premium: bool


class SubscriptionFeaturesResponse(BaseModel):
    plan_code: str
    status: str
    has_pro_access: bool
    features: list[FeatureAccess]
