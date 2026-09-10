from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RevokeSessionsResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SecurityEventResponse(BaseModel):
    event_type: str
    description: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AccountDeleteRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    confirmation: str = Field(min_length=6, max_length=40)


class DataExportResponse(BaseModel):
    exported_at: datetime
    data: dict[str, Any]
