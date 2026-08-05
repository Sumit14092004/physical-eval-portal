import uuid
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, ForeignKey, Enum as SAEnum, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import TestCategory, ComparisonType, GradeLevel


class PhysicalActivity(Base):
    """
    One row per activity within a test category, e.g.
    (BPET, "5 km Race"), (PPT, "Chin up"), (PPT, "Push up" — 40-45 only), etc.
    Kept separate from the threshold table so an activity can be reused
    across age bands without repeating its name/unit/comparison type.
    """
    __tablename__ = "physical_activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_category: Mapped[TestCategory] = mapped_column(SAEnum(TestCategory, name="test_category", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "5 km Race", "V-Rope", "Chin up"...
    unit: Mapped[str] = mapped_column(String(20), nullable=False)   # "min", "mtr", "feet", "sec", "count"
    comparison_type: Mapped[ComparisonType] = mapped_column(
        SAEnum(ComparisonType, name="comparison_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )

    standards: Mapped[list["PhysicalStandard"]] = relationship(back_populates="activity")


class PhysicalStandard(Base):
    """
    The exact Ex/Good/Sat thresholds per activity per age band, seeded
    directly from the official BPET/PPT tables. This is a reference
    table, not hardcoded logic -- so if standards are revised (new
    circular, new age band, new personnel category) an admin updates
    this table and the grading engine picks it up automatically.
    """
    __tablename__ = "physical_standards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("physical_activities.id"), nullable=False, index=True)
    personnel_category: Mapped[str] = mapped_column(String(50), default="GD Personnel")
    age_min: Mapped[int] = mapped_column(nullable=False)
    age_max: Mapped[int] = mapped_column(nullable=False)
    excellent_value: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    good_value: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    satisfactory_value: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    # some activities are "-" (not applicable) for certain age bands, e.g.
    # Toe touch / B-K sit-up not applicable 30-40; handled by leaving values null.

    activity: Mapped["PhysicalActivity"] = relationship(back_populates="standards")


class PhysicalTestResult(Base):
    """
    A single trainee's raw performance on one activity on one test date.
    Grade is computed by the grading service (not stored redundantly
    beyond a cached column for fast reads) by comparing raw_value
    against the matching PhysicalStandard row for the trainee's age
    band + activity.
    """
    __tablename__ = "physical_test_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trainees.id"), nullable=False, index=True)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("physical_activities.id"), nullable=False, index=True)
    test_date: Mapped[date] = mapped_column(Date, nullable=False)
    raw_value: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    computed_grade: Mapped[GradeLevel | None] = mapped_column(
        SAEnum(GradeLevel, name="grade_level", values_callable=lambda obj: [e.value for e in obj]), nullable=True
    )  # cached at write time by the grading service; recomputable anytime
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    trainee: Mapped["Trainee"] = relationship()
    activity: Mapped["PhysicalActivity"] = relationship()
