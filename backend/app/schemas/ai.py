from pydantic import BaseModel, Field


class AIAskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1200)


class AIAskResponse(BaseModel):
    answer: str
    provider: str
    model: str
