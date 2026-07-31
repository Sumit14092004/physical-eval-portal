import uuid
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, ForeignKey, Enum as SAEnum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import IndoorOutdoor


class TrainingRecord(Base):
    """
    Maps directly to section 13 (Training Module) of the spec:
    subject, instructor, indoor/outdoor, attendance, practical
    performance, and the drill/PT/weapon/firing/obstacle/tactical
    performance fields.
    """
    __tablename__ = "training_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trainees.id"), nullable=False, index=True)
    subject_name: Mapped[str] = mapped_column(String(150), nullable=False)
    instructor_name: Mapped[str] = mapped_column(String(150), nullable=False)
    indoor_outdoor: Mapped[IndoorOutdoor] = mapped_column(SAEnum(IndoorOutdoor, name="indoor_outdoor"), nullable=False)
    periods_attended: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    periods_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    practical_performance: Mapped[str | None] = mapped_column(Text, nullable=True)
    bpet_ppt_performance: Mapped[str | None] = mapped_column(Text, nullable=True)

    drill_performance: Mapped[str | None] = mapped_column(Text, nullable=True)
    pt_performance: Mapped[str | None] = mapped_column(Text, nullable=True)
    weapon_training: Mapped[str | None] = mapped_column(Text, nullable=True)
    firing_practice: Mapped[str | None] = mapped_column(Text, nullable=True)
    obstacle_training: Mapped[str | None] = mapped_column(Text, nullable=True)
    tactical_training: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    trainee: Mapped["Trainee"] = relationship()
