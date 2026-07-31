import uuid
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, ForeignKey, Enum as SAEnum, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import ResultStatus

# Percentage/Rank fields below are intentionally NOT stored as the
# source of truth -- they're computed columns refreshed by the ranking
# service (via Postgres window functions) and cached here for fast
# reads on dashboards/leaderboards. This avoids read-time aggregation
# over 150k+ rows on every page load while keeping a single
# recomputation path if standards or marks are corrected.


class WeeklyTest(Base):
    __tablename__ = "weekly_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trainees.id"), nullable=False, index=True)
    test_date: Mapped[date] = mapped_column(Date, nullable=False)
    subject: Mapped[str] = mapped_column(String(150), nullable=False)
    maximum_marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    marks_obtained: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)  # auto-calculated
    result_status: Mapped[ResultStatus] = mapped_column(SAEnum(ResultStatus, name="result_status"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MonthlyTest(Base):
    __tablename__ = "monthly_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trainees.id"), nullable=False, index=True)
    month: Mapped[date] = mapped_column(Date, nullable=False)  # first day of the month, e.g. 2026-08-01
    subject_wise_marks: Mapped[dict] = mapped_column(JSONB, nullable=False)  # {"Math": 80, "Drill": 70, ...}
    aggregate: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)  # within batch, computed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class QuarterlyExam(Base):
    __tablename__ = "quarterly_exams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trainees.id"), nullable=False, index=True)
    quarter: Mapped[str] = mapped_column(String(10), nullable=False)  # "Q1", "Q2", ...
    written_marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    practical_marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    pt_marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    firing_marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    total_marks: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class FinalExamination(Base):
    __tablename__ = "final_examinations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trainees.id"), unique=True, nullable=False, index=True)

    written_examination: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    practical_examination: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    pt_test: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    bpet: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    ppt: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    firing_classification: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    outdoor_assessment: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    indoor_assessment: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    field_craft: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    battle_craft: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    drill_test: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    weapon_test: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)

    aggregate_marks: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)  # auto-calculated
    final_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)  # auto-calculated
    merit_position: Mapped[int | None] = mapped_column(Integer, nullable=True)  # computed, batch-wide

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
