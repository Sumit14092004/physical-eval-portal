import uuid
from datetime import date, datetime
from pydantic import BaseModel


class FpetActivityOut(BaseModel):
    name: str
    max_marks: float


class FpetTemplateOut(BaseModel):
    trainee_id: uuid.UUID
    gender: str
    age: int
    age_band: str
    activities: list[FpetActivityOut]
    max_total: float


class FpetResultIn(BaseModel):
    trainee_id: uuid.UUID
    test_date: date
    raw_performances: dict[str, str] = {}  # {"3.2 KMS Run": "14:30", "Push Ups": "40"}
    marks: dict[str, float]  # {"3.2 KMS Run": 10, ...} -- must match the template exactly


class FpetResultOut(BaseModel):
    id: uuid.UUID
    trainee_id: uuid.UUID
    test_date: date
    gender: str
    age_band: str
    raw_performances: dict[str, str]
    marks: dict[str, float]
    total_marks: float
    max_total: float
    percentage: float
    grade: str
    created_at: datetime

    class Config:
        from_attributes = True
