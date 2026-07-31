import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.base import get_db
from app.core.deps import require_roles, get_current_user_payload
from app.models.enums import UserRole
from app.models.physical_evaluation import PhysicalActivity, PhysicalTestResult
from app.models.user import Trainee
from app.services.grading import grade_result

router = APIRouter(prefix="/api/v1/physical-evaluation", tags=["physical-evaluation"])


class RecordResultIn(BaseModel):
    trainee_id: uuid.UUID
    activity_id: uuid.UUID
    test_date: date
    raw_value: float
    remark: str | None = None


class RecordResultOut(BaseModel):
    id: uuid.UUID
    computed_grade: str | None
    raw_value: float

    class Config:
        from_attributes = True


class ActivityOut(BaseModel):
    id: uuid.UUID
    test_category: str
    name: str
    unit: str
    comparison_type: str

    class Config:
        from_attributes = True


@router.get("/activities", response_model=list[ActivityOut])
async def list_activities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PhysicalActivity).order_by(PhysicalActivity.test_category, PhysicalActivity.name))
    return result.scalars().all()


@router.post(
    "/results",
    response_model=RecordResultOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.INSTRUCTOR))],
)
async def record_result(
    payload: RecordResultIn,
    db: AsyncSession = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload),
):
    trainee = (await db.execute(select(Trainee).where(Trainee.id == payload.trainee_id))).scalar_one_or_none()
    if trainee is None:
        raise HTTPException(status_code=404, detail="Trainee not found")

    activity = (await db.execute(
        select(PhysicalActivity).where(PhysicalActivity.id == payload.activity_id)
    )).scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    grade = await grade_result(
        db, activity, payload.raw_value, trainee.date_of_birth,
        trainee.personnel_category, payload.test_date,
    )

    record = PhysicalTestResult(
        trainee_id=payload.trainee_id,
        activity_id=payload.activity_id,
        test_date=payload.test_date,
        raw_value=payload.raw_value,
        computed_grade=grade,
        remark=payload.remark,
        recorded_by=uuid.UUID(user_payload["sub"]),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get(
    "/results/{trainee_id}",
    response_model=list[RecordResultOut],
)
async def get_trainee_results(trainee_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PhysicalTestResult).where(PhysicalTestResult.trainee_id == trainee_id)
    )
    return result.scalars().all()
