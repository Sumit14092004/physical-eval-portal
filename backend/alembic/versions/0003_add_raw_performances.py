"""add raw_performances to fpet_results

Revision ID: 0003_raw_perf
Revises: 0002_fpet_results
Create Date: 2026-08-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_raw_perf"
down_revision = "0002_fpet_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    columns = [col['name'] for col in inspector.get_columns('fpet_results')]
    if "raw_performances" not in columns:
        op.add_column("fpet_results", sa.Column("raw_performances", postgresql.JSONB(), server_default='{}', nullable=False))


def downgrade() -> None:
    op.drop_column("fpet_results", "raw_performances")
