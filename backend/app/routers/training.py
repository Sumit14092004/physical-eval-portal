import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.core.deps import require_roles
from app.models.enums import UserRole
from app.models.training import TrainingRecord
from app.schemas.training import TrainingRecordIn, TrainingRecordOut

router = APIRouter(prefix="/api/v1/training-records", tags=["training-records"])


@router.post(
    "",
    response_model=TrainingRecordOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.INSTRUCTOR))],
)
async def create_training_record(payload: TrainingRecordIn, db: AsyncSession = Depends(get_db)):
    record = TrainingRecord(**payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{trainee_id}", response_model=list[TrainingRecordOut])
async def list_training_records(trainee_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingRecord).where(TrainingRecord.trainee_id == trainee_id))
    return result.scalars().all()


@router.put(
    "/{record_id}",
    response_model=TrainingRecordOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.INSTRUCTOR))],
)
async def update_training_record(record_id: uuid.UUID, payload: TrainingRecordIn, db: AsyncSession = Depends(get_db)):
    record = (await db.execute(select(TrainingRecord).where(TrainingRecord.id == record_id))).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Training record not found")
    for field, value in payload.model_dump().items():
        setattr(record, field, value)
    await db.commit()
    await db.refresh(record)
    return record
