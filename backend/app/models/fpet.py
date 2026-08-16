import uuid
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class FpetResult(Base):
    """
    One FPET (Field Physical Efficiency Test) attempt for a trainee.

    Unlike the older BPET/PPT physical_test_results table (raw
    performance value -> auto-graded against age-band thresholds), FPET
    marks are entered directly per activity -- exactly matching the
    paper form, where the instructor already has the scored value
    (0-10, 0-15, etc.) for each event, not a raw time/count to convert.

    gender/age_band are snapshotted at submission time (not re-derived
    from the trainee record later) so a result stays interpretable even
    if the trainee's DOB is corrected afterward.
    """
    __tablename__ = "fpet_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trainees.id"), nullable=False, index=True)
    test_date: Mapped[date] = mapped_column(Date, nullable=False)

    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    age_band: Mapped[str] = mapped_column(String(20), nullable=False)  # "below_35" | "35_40" | "40_45" | "female"

    marks: Mapped[dict] = mapped_column(JSONB, nullable=False)  # {"3.2 KMS Run": 10, "M/Rope": 8, ...}
    total_marks: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    max_total: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)  # placeholder bands -- see app/services/fpet.py

    recorded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    trainee: Mapped["Trainee"] = relationship()
