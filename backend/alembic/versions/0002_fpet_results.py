"""add fpet_results table

Revision ID: 0002_fpet_results
Revises: 0001_initial
Create Date: 2026-08-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_fpet_results"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "fpet_results" in inspector.get_table_names():
        return  # idempotent, same reasoning as 0001 -- see that file's comment

    op.create_table(
        "fpet_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trainees.id"), nullable=False),
        sa.Column("test_date", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(20), nullable=False),
        sa.Column("age_band", sa.String(20), nullable=False),
        sa.Column("marks", postgresql.JSONB(), nullable=False),
        sa.Column("total_marks", sa.Numeric(6, 2), nullable=False),
        sa.Column("max_total", sa.Numeric(6, 2), nullable=False),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("grade", sa.String(20), nullable=False),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_fpet_results_trainee_id", "fpet_results", ["trainee_id"])


def downgrade() -> None:
    op.drop_table("fpet_results")
