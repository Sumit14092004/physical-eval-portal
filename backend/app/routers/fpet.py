import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.core.deps import require_roles, get_current_user_payload
from app.models.enums import UserRole
from app.models.user import Trainee
from app.models.fpet import FpetResult
from app.schemas.fpet import (
    FpetTemplateOut, FpetActivityOut, FpetResultIn, FpetResultOut,
)
from app.services.fpet import resolve_age_band, get_template, grade_from_marks, compute_age

router = APIRouter(prefix="/api/v1/fpet", tags=["fpet"])


async def _get_trainee_or_404(db: AsyncSession, trainee_id: uuid.UUID) -> Trainee:
    trainee = (await db.execute(select(Trainee).where(Trainee.id == trainee_id))).scalar_one_or_none()
    if trainee is None:
        raise HTTPException(status_code=404, detail="Trainee not found")
    return trainee


@router.get("/template/{trainee_id}", response_model=FpetTemplateOut)
async def get_fpet_template(trainee_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Auto-resolves gender + age band from the trainee's own record and
    returns the fixed, ordered activity list -- this is what lets the
    frontend pre-load marks-entry fields with no per-activity dropdown.
    """
    trainee = await _get_trainee_or_404(db, trainee_id)
    age_band = resolve_age_band(trainee.gender, trainee.date_of_birth)
    template = get_template(age_band)
    return FpetTemplateOut(
        trainee_id=trainee.id,
        gender=trainee.gender,
        age=compute_age(trainee.date_of_birth),
        age_band=age_band,
        activities=[FpetActivityOut(name=n, max_marks=m) for n, m in template],
        max_total=sum(m for _, m in template),
    )


@router.post(
    "/results",
    response_model=FpetResultOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.INSTRUCTOR))],
)
async def record_fpet_result(
    payload: FpetResultIn,
    db: AsyncSession = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload),
):
    trainee = await _get_trainee_or_404(db, payload.trainee_id)

    # Age band/template is re-resolved server-side from the trainee
    # record, not trusted from the client -- the marks a client submits
    # are validated against exactly this template so a mismatched or
    # tampered payload can't silently score against the wrong sequence.
    age_band = resolve_age_band(trainee.gender, trainee.date_of_birth)
    template = get_template(age_band)
    template_names = {name for name, _ in template}
    max_by_name = {name: max_marks for name, max_marks in template}

    if set(payload.marks.keys()) != template_names:
        raise HTTPException(
            status_code=400,
            detail=f"Marks must be provided for exactly these activities: {sorted(template_names)}",
        )
    for name, value in payload.marks.items():
        if value < 0 or value > max_by_name[name]:
            raise HTTPException(
                status_code=400,
                detail=f"'{name}' must be between 0 and {max_by_name[name]}",
            )

    total, max_total, percentage, grade = grade_from_marks(payload.marks, template)

    record = FpetResult(
        trainee_id=payload.trainee_id,
        test_date=payload.test_date,
        gender=trainee.gender,
        age_band=age_band,
        raw_performances=payload.raw_performances,
        marks=payload.marks,
        total_marks=total,
        max_total=max_total,
        percentage=percentage,
        grade=grade,
        recorded_by=uuid.UUID(user_payload["sub"]),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/results/{trainee_id}", response_model=list[FpetResultOut])
async def list_fpet_results(trainee_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FpetResult).where(FpetResult.trainee_id == trainee_id).order_by(FpetResult.test_date.desc())
    )
    return result.scalars().all()
