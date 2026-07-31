import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.enums import IndoorOutdoor


class TrainingRecordIn(BaseModel):
    trainee_id: uuid.UUID
    subject_name: str
    instructor_name: str
    indoor_outdoor: IndoorOutdoor
    periods_attended: int = 0
    periods_total: int = 0
    practical_performance: str | None = None
    bpet_ppt_performance: str | None = None
    drill_performance: str | None = None
    pt_performance: str | None = None
    weapon_training: str | None = None
    firing_practice: str | None = None
    obstacle_training: str | None = None
    tactical_training: str | None = None


class TrainingRecordOut(TrainingRecordIn):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
