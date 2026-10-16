from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.llm.schemas import FactsSchema, GuidanceResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CaseCreate(BaseModel):
    query_text: str = Field(min_length=10, max_length=5000, description="Describe your legal problem")


class ReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    act: str
    section: str
    page: int
    chunk_text: str
    score: float


class CaseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query_text: str
    confidence: str
    created_at: datetime


class CaseDetail(CaseSummary):
    facts: FactsSchema
    response: GuidanceResponse
    references: list[ReferenceOut]
