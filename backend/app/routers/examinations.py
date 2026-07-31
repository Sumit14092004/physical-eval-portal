import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.core.deps import require_roles
from app.models.enums import UserRole, ResultStatus
from app.models.user import Trainee, User
from app.models.examination import WeeklyTest, MonthlyTest, QuarterlyExam, FinalExamination
from app.schemas.examination import (
    WeeklyTestIn, WeeklyTestOut,
    MonthlyTestIn, MonthlyTestOut,
    QuarterlyExamIn, QuarterlyExamOut,
    FinalExaminationIn, FinalExaminationOut,
    MeritListEntry,
)
from app.tasks.ranking_tasks import (
    recompute_monthly_ranks_task,
    recompute_quarterly_ranks_task,
    recompute_final_exam_ranks_task,
)

router = APIRouter(prefix="/api/v1/exams", tags=["exams"])

INSTRUCTOR_ROLES = [Depends(require_roles(UserRole.ADMIN, UserRole.INSTRUCTOR))]

# Pass mark threshold for weekly tests -- adjust to your academy's actual
# policy; kept as a constant here rather than buried in the handler logic.
WEEKLY_PASS_PERCENTAGE = 40.0


async def _get_trainee_or_404(db: AsyncSession, trainee_id: uuid.UUID) -> Trainee:
    trainee = (await db.execute(select(Trainee).where(Trainee.id == trainee_id))).scalar_one_or_none()
    if trainee is None:
        raise HTTPException(status_code=404, detail="Trainee not found")
    return trainee


# ---------- Weekly ----------

@router.post("/weekly", response_model=WeeklyTestOut, dependencies=INSTRUCTOR_ROLES)
async def create_weekly_test(payload: WeeklyTestIn, db: AsyncSession = Depends(get_db)):
    await _get_trainee_or_404(db, payload.trainee_id)

    percentage = round((payload.marks_obtained / payload.maximum_marks) * 100, 2) if payload.maximum_marks else 0.0
    status = ResultStatus.PASS if percentage >= WEEKLY_PASS_PERCENTAGE else ResultStatus.FAIL

    record = WeeklyTest(
        trainee_id=payload.trainee_id,
        test_date=payload.test_date,
        subject=payload.subject,
        maximum_marks=payload.maximum_marks,
        marks_obtained=payload.marks_obtained,
        percentage=percentage,
        result_status=status,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/weekly/{trainee_id}", response_model=list[WeeklyTestOut])
async def list_weekly_tests(trainee_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeeklyTest).where(WeeklyTest.trainee_id == trainee_id))
    return result.scalars().all()


# ---------- Monthly ----------

@router.post("/monthly", response_model=MonthlyTestOut, dependencies=INSTRUCTOR_ROLES)
async def create_monthly_test(payload: MonthlyTestIn, db: AsyncSession = Depends(get_db)):
    trainee = await _get_trainee_or_404(db, payload.trainee_id)

    aggregate = round(sum(payload.subject_wise_marks.values()), 2)

    record = MonthlyTest(
        trainee_id=payload.trainee_id,
        month=payload.month,
        subject_wise_marks=payload.subject_wise_marks,
        aggregate=aggregate,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # Rank recompute now runs as a background Celery task rather than
    # inline -- at 150k+ scale, many instructors submitting marks
    # concurrently within the same batch/month shouldn't all block on
    # (and contend for locks during) the same rank-recompute query.
    # The trade-off: `rank` on the object returned here reflects the
    # state before this submission, not after -- the frontend re-fetches
    # to see the settled rank once the task completes (typically <1s).
    recompute_monthly_ranks_task.delay(str(trainee.batch_id), str(payload.month))
    return record


@router.get("/monthly/{trainee_id}", response_model=list[MonthlyTestOut])
async def list_monthly_tests(trainee_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MonthlyTest).where(MonthlyTest.trainee_id == trainee_id))
    return result.scalars().all()


# ---------- Quarterly ----------

@router.post("/quarterly", response_model=QuarterlyExamOut, dependencies=INSTRUCTOR_ROLES)
async def create_quarterly_exam(payload: QuarterlyExamIn, db: AsyncSession = Depends(get_db)):
    trainee = await _get_trainee_or_404(db, payload.trainee_id)

    total_marks = round(
        payload.written_marks + payload.practical_marks + payload.pt_marks + payload.firing_marks, 2
    )
    percentage = round((total_marks / payload.max_total_marks) * 100, 2) if payload.max_total_marks else 0.0

    record = QuarterlyExam(
        trainee_id=payload.trainee_id,
        quarter=payload.quarter,
        written_marks=payload.written_marks,
        practical_marks=payload.practical_marks,
        pt_marks=payload.pt_marks,
        firing_marks=payload.firing_marks,
        total_marks=total_marks,
        percentage=percentage,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    recompute_quarterly_ranks_task.delay(str(trainee.batch_id), payload.quarter)
    return record


@router.get("/quarterly/{trainee_id}", response_model=list[QuarterlyExamOut])
async def list_quarterly_exams(trainee_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QuarterlyExam).where(QuarterlyExam.trainee_id == trainee_id))
    return result.scalars().all()


# ---------- Final ----------

@router.post("/final", response_model=FinalExaminationOut, dependencies=INSTRUCTOR_ROLES)
async def create_final_examination(payload: FinalExaminationIn, db: AsyncSession = Depends(get_db)):
    trainee = await _get_trainee_or_404(db, payload.trainee_id)

    component_fields = [
        payload.written_examination, payload.practical_examination, payload.pt_test,
        payload.bpet, payload.ppt, payload.firing_classification,
        payload.outdoor_assessment, payload.indoor_assessment,
        payload.field_craft, payload.battle_craft, payload.drill_test, payload.weapon_test,
    ]
    aggregate_marks = round(sum(component_fields), 2)
    final_percentage = (
        round((aggregate_marks / payload.max_aggregate_marks) * 100, 2)
        if payload.max_aggregate_marks else 0.0
    )

    existing = (await db.execute(
        select(FinalExamination).where(FinalExamination.trainee_id == payload.trainee_id)
    )).scalar_one_or_none()

    data = payload.model_dump(exclude={"max_aggregate_marks"})
    if existing:
        for field, value in data.items():
            setattr(existing, field, value)
        existing.aggregate_marks = aggregate_marks
        existing.final_percentage = final_percentage
        record = existing
    else:
        record = FinalExamination(**data, aggregate_marks=aggregate_marks, final_percentage=final_percentage)
        db.add(record)

    await db.commit()
    await db.refresh(record)

    recompute_final_exam_ranks_task.delay(str(trainee.batch_id))
    return record


@router.get("/final/merit-list", response_model=list[MeritListEntry])
async def get_merit_list(batch_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(FinalExamination, Trainee.enrollment_number, User.full_name)
        .join(Trainee, Trainee.id == FinalExamination.trainee_id)
        .join(User, User.id == Trainee.user_id)
        .where(Trainee.batch_id == batch_id)
        .order_by(FinalExamination.merit_position.asc().nulls_last())
    )
    result = await db.execute(stmt)
    return [
        MeritListEntry(
            merit_position=fe.merit_position,
            trainee_id=fe.trainee_id,
            trainee_name=full_name,
            enrollment_number=enrollment_number,
            aggregate_marks=float(fe.aggregate_marks),
            final_percentage=float(fe.final_percentage),
        )
        for fe, enrollment_number, full_name in result.all()
    ]


@router.get("/final/{trainee_id}", response_model=FinalExaminationOut)
async def get_final_examination(trainee_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    record = (await db.execute(
        select(FinalExamination).where(FinalExamination.trainee_id == trainee_id)
    )).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Final examination record not found")
    return record
