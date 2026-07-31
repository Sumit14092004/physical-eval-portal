import csv
import io
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.base import get_db
from app.core.deps import require_roles, get_current_user_payload
from app.models.enums import UserRole
from app.models.user import User, Trainee, Batch
from app.core.security import hash_password
from app.schemas.org import BatchIn, BatchOut, TrainingCreateIn, TraineeOut

router = APIRouter(prefix="/api/v1/org", tags=["organization"])


@router.get("/trainees/me", response_model=TraineeOut)
async def get_my_trainee_profile(
    db: AsyncSession = Depends(get_db),
    user_payload: dict = Depends(get_current_user_payload),
):
    """
    Lets a logged-in trainee resolve their own Trainee row (and hence
    their own trainee_id) from their JWT alone, without needing to know
    or be given a UUID by anyone else -- that's how the read-only
    "My Records" screens find out whose data to fetch.
    """
    stmt = (
        select(Trainee, User.full_name)
        .join(User, User.id == Trainee.user_id)
        .where(Trainee.user_id == uuid.UUID(user_payload["sub"]))
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="No trainee profile found for this account")
    t, full_name = row
    return TraineeOut(
        id=t.id,
        enrollment_number=t.enrollment_number,
        full_name=full_name,
        batch_id=t.batch_id,
        date_of_birth=t.date_of_birth,
        gender=t.gender,
        personnel_category=t.personnel_category,
    )


# ---------- Batches ----------

@router.post("/batches", response_model=BatchOut, dependencies=[Depends(require_roles(UserRole.ADMIN))])
async def create_batch(payload: BatchIn, db: AsyncSession = Depends(get_db)):
    batch = Batch(**payload.model_dump())
    db.add(batch)
    await db.commit()
    await db.refresh(batch)
    return batch


@router.get("/batches", response_model=list[BatchOut])
async def list_batches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Batch).order_by(Batch.start_date.desc()))
    return result.scalars().all()


# ---------- Trainees ----------

@router.post(
    "/trainees",
    response_model=TraineeOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def create_trainee(payload: TrainingCreateIn, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.TRAINEE,
    )
    db.add(user)
    await db.flush()  # assign user.id before creating the trainee row

    trainee = Trainee(
        user_id=user.id,
        batch_id=payload.batch_id,
        enrollment_number=payload.enrollment_number,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        personnel_category=payload.personnel_category,
    )
    db.add(trainee)
    await db.commit()
    await db.refresh(trainee)

    return TraineeOut(
        id=trainee.id,
        enrollment_number=trainee.enrollment_number,
        full_name=user.full_name,
        batch_id=trainee.batch_id,
        date_of_birth=trainee.date_of_birth,
        gender=trainee.gender,
        personnel_category=trainee.personnel_category,
    )


@router.get("/trainees", response_model=list[TraineeOut])
async def list_trainees(batch_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Trainee, User.full_name).join(User, User.id == Trainee.user_id)
    if batch_id:
        stmt = stmt.where(Trainee.batch_id == batch_id)
    result = await db.execute(stmt)
    return [
        TraineeOut(
            id=t.id,
            enrollment_number=t.enrollment_number,
            full_name=full_name,
            batch_id=t.batch_id,
            date_of_birth=t.date_of_birth,
            gender=t.gender,
            personnel_category=t.personnel_category,
        )
        for t, full_name in result.all()
    ]


# ---------- Bulk import ----------

class ImportRowError(BaseModel):
    row: int
    email: str | None = None
    error: str


class BulkImportResult(BaseModel):
    created: int
    skipped: int
    errors: list[ImportRowError]


REQUIRED_COLUMNS = {
    "email", "password", "full_name", "enrollment_number",
    "date_of_birth", "gender",
}


@router.post(
    "/trainees/bulk-import",
    response_model=BulkImportResult,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def bulk_import_trainees(
    batch_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    CSV columns required: email, password, full_name, enrollment_number,
    date_of_birth (YYYY-MM-DD), gender. Optional: personnel_category.

    Designed for onboarding at scale: existing emails/enrollment numbers
    in the batch are pre-loaded once, so duplicate checks are in-memory
    set lookups rather than a DB round-trip per row. Commits happen in
    chunks so one bad row in a 150k-row file doesn't roll back everything
    already processed, and a huge file doesn't hold one giant open
    transaction.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    batch = (await db.execute(select(Batch).where(Batch.id == batch_id))).scalar_one_or_none()
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    raw = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))

    missing_cols = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required columns: {', '.join(sorted(missing_cols))}",
        )

    existing_emails = set(
        (await db.execute(select(User.email))).scalars().all()
    )
    existing_enrollments = set(
        (await db.execute(select(Trainee.enrollment_number))).scalars().all()
    )

    created = 0
    skipped = 0
    errors: list[ImportRowError] = []
    CHUNK_SIZE = 500
    pending = 0

    for row_num, row in enumerate(reader, start=2):  # header is row 1
        email = (row.get("email") or "").strip().lower()
        enrollment_number = (row.get("enrollment_number") or "").strip()

        try:
            if not email or not enrollment_number:
                raise ValueError("email and enrollment_number are required")
            if email in existing_emails:
                skipped += 1
                continue
            if enrollment_number in existing_enrollments:
                skipped += 1
                continue

            from datetime import date as date_cls
            dob = date_cls.fromisoformat((row.get("date_of_birth") or "").strip())

            user = User(
                email=email,
                hashed_password=hash_password((row.get("password") or "").strip() or "ChangeMe123!"),
                full_name=(row.get("full_name") or "").strip(),
                role=UserRole.TRAINEE,
            )
            db.add(user)
            await db.flush()

            trainee = Trainee(
                user_id=user.id,
                batch_id=batch_id,
                enrollment_number=enrollment_number,
                date_of_birth=dob,
                gender=(row.get("gender") or "").strip(),
                personnel_category=(row.get("personnel_category") or "GD Personnel").strip(),
            )
            db.add(trainee)

            existing_emails.add(email)
            existing_enrollments.add(enrollment_number)
            created += 1
            pending += 1

            if pending >= CHUNK_SIZE:
                await db.commit()
                pending = 0

        except Exception as exc:
            await db.rollback()
            errors.append(ImportRowError(row=row_num, email=email or None, error=str(exc)))

    if pending:
        await db.commit()

    return BulkImportResult(created=created, skipped=skipped, errors=errors)
