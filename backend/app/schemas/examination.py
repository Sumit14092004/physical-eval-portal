import uuid
from datetime import date, datetime
from pydantic import BaseModel
from app.models.enums import ResultStatus


class WeeklyTestIn(BaseModel):
    trainee_id: uuid.UUID
    test_date: date
    subject: str
    maximum_marks: float
    marks_obtained: float


class WeeklyTestOut(WeeklyTestIn):
    id: uuid.UUID
    percentage: float
    result_status: ResultStatus
    created_at: datetime

    class Config:
        from_attributes = True


class MonthlyTestIn(BaseModel):
    trainee_id: uuid.UUID
    month: date
    subject_wise_marks: dict[str, float]


class MonthlyTestOut(MonthlyTestIn):
    id: uuid.UUID
    aggregate: float
    rank: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class QuarterlyExamIn(BaseModel):
    trainee_id: uuid.UUID
    quarter: str
    written_marks: float
    practical_marks: float
    pt_marks: float
    firing_marks: float
    max_total_marks: float = 400  # used to compute percentage; adjust to your actual max


class QuarterlyExamOut(BaseModel):
    id: uuid.UUID
    trainee_id: uuid.UUID
    quarter: str
    written_marks: float
    practical_marks: float
    pt_marks: float
    firing_marks: float
    total_marks: float
    percentage: float
    rank: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class FinalExaminationIn(BaseModel):
    trainee_id: uuid.UUID
    written_examination: float
    practical_examination: float
    pt_test: float
    bpet: float
    ppt: float
    firing_classification: float
    outdoor_assessment: float
    indoor_assessment: float
    field_craft: float
    battle_craft: float
    drill_test: float
    weapon_test: float
    max_aggregate_marks: float = 1200  # adjust to your actual scheme's max total


class FinalExaminationOut(BaseModel):
    id: uuid.UUID
    trainee_id: uuid.UUID
    written_examination: float
    practical_examination: float
    pt_test: float
    bpet: float
    ppt: float
    firing_classification: float
    outdoor_assessment: float
    indoor_assessment: float
    field_craft: float
    battle_craft: float
    drill_test: float
    weapon_test: float
    aggregate_marks: float
    final_percentage: float
    merit_position: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class MeritListEntry(BaseModel):
    merit_position: int | None
    trainee_id: uuid.UUID
    trainee_name: str
    enrollment_number: str
    aggregate_marks: float
    final_percentage: float
