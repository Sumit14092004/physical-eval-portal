import uuid
from datetime import date
from pydantic import BaseModel, EmailStr


class BatchIn(BaseModel):
    name: str
    start_date: date
    end_date: date | None = None


class BatchOut(BatchIn):
    id: uuid.UUID

    class Config:
        from_attributes = True


class TrainingCreateIn(BaseModel):
    """
    Creates the User + Trainee rows together, since a trainee can't
    exist without a login. Admin-only.
    """
    email: EmailStr
    password: str
    full_name: str
    batch_id: uuid.UUID
    enrollment_number: str
    date_of_birth: date
    gender: str
    personnel_category: str = "GD Personnel"


class TraineeOut(BaseModel):
    id: uuid.UUID
    enrollment_number: str
    full_name: str
    batch_id: uuid.UUID
    date_of_birth: date
    gender: str
    personnel_category: str

    class Config:
        from_attributes = True
