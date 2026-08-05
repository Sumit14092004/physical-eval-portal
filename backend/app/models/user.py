import uuid
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import UserRole


class User(Base):
    """
    Every login (admin, instructor, trainee) is a User row.
    Trainee-specific fields live in the Trainee table (1:1), so we don't
    bloat the auth table and can add other role profiles later without
    touching this table.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role", values_callable=lambda obj: [e.value for e in obj]), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    trainee_profile: Mapped["Trainee"] = relationship(back_populates="user", uselist=False)


class Batch(Base):
    """
    A training cohort/intake. Physical standards, ranks, and reports are
    almost always scoped to a batch, so this is a first-class entity
    rather than a free-text field -- makes partitioned rank queries and
    batch-level reporting fast even at 150k+ trainee scale.
    """
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "GD Constable Batch 2026-A"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    trainees: Mapped[list["Trainee"]] = relationship(back_populates="batch")


class Trainee(Base):
    __tablename__ = "trainees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("batches.id"), nullable=False, index=True)
    enrollment_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    personnel_category: Mapped[str] = mapped_column(String(50), default="GD Personnel")
    # age_group is derived at query time from date_of_birth (18-30 / 30-40 / 40-45 / 45-50)
    # via a service function -- not stored, so it never goes stale.

    user: Mapped["User"] = relationship(back_populates="trainee_profile")
    batch: Mapped["Batch"] = relationship(back_populates="trainees")
