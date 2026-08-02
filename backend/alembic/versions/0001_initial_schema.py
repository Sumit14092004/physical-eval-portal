"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" in inspector.get_table_names():
        # A previous deploy attempt (e.g. Render's auto-deploy-on-push
        # racing a manual redeploy of the same commit) already got this
        # far. This migration is all-or-nothing, so if the first table
        # exists, treat the whole thing as already applied rather than
        # erroring out on every subsequent CREATE TABLE.
        return

    # create_type=False on all of these: we create the actual Postgres
    # types ourselves via the DO blocks above. Without this,
    # SQLAlchemy's ENUM defaults to create_type=True and silently emits
    # its own bare `CREATE TYPE` as a side effect of create_table()
    # below -- a second, unprotected creation attempt that collides
    # with the one we just made idempotent.
    user_role = postgresql.ENUM("admin", "instructor", "trainee", name="user_role", create_type=False)
    test_category = postgresql.ENUM("bpet", "ppt", name="test_category", create_type=False)
    comparison_type = postgresql.ENUM("lower_is_better", "higher_is_better", name="comparison_type", create_type=False)
    grade_level = postgresql.ENUM("excellent", "good", "satisfactory", "fail", name="grade_level", create_type=False)
    result_status = postgresql.ENUM("pass", "fail", name="result_status", create_type=False)
    indoor_outdoor = postgresql.ENUM("indoor", "outdoor", name="indoor_outdoor", create_type=False)

    # Raw idempotent DDL instead of ENUM(...).create(bind, checkfirst=True):
    # checkfirst does a SELECT-then-CREATE, which has a race window if two
    # deploy attempts overlap (e.g. Render's auto-deploy-on-push firing
    # while a manual deploy from the same commit is also running) -- both
    # can pass the check before either commits the CREATE, and the second
    # CREATE then fails with "already exists". Wrapping in a DO block with
    # an exception handler makes this genuinely idempotent regardless of
    # timing, not just "usually fine."
    for enum_name, values in [
        ("user_role", ("admin", "instructor", "trainee")),
        ("test_category", ("bpet", "ppt")),
        ("comparison_type", ("lower_is_better", "higher_is_better")),
        ("grade_level", ("excellent", "good", "satisfactory", "fail")),
        ("result_status", ("pass", "fail")),
        ("indoor_outdoor", ("indoor", "outdoor")),
    ]:
        values_sql = ", ".join(f"'{v}'" for v in values)
        op.execute(f"""
            DO $$ BEGIN
                CREATE TYPE {enum_name} AS ENUM ({values_sql});
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "trainees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("batches.id"), nullable=False),
        sa.Column("enrollment_number", sa.String(50), nullable=False, unique=True),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(20), nullable=False),
        sa.Column("personnel_category", sa.String(50), server_default="GD Personnel"),
    )
    op.create_index("ix_trainees_batch_id", "trainees", ["batch_id"])
    op.create_index("ix_trainees_enrollment_number", "trainees", ["enrollment_number"])

    op.create_table(
        "physical_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("test_category", test_category, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("comparison_type", comparison_type, nullable=False),
    )

    op.create_table(
        "physical_standards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("physical_activities.id"), nullable=False),
        sa.Column("personnel_category", sa.String(50), server_default="GD Personnel"),
        sa.Column("age_min", sa.Integer(), nullable=False),
        sa.Column("age_max", sa.Integer(), nullable=False),
        sa.Column("excellent_value", sa.Numeric(6, 2), nullable=True),
        sa.Column("good_value", sa.Numeric(6, 2), nullable=True),
        sa.Column("satisfactory_value", sa.Numeric(6, 2), nullable=True),
    )
    op.create_index("ix_physical_standards_activity_id", "physical_standards", ["activity_id"])

    op.create_table(
        "physical_test_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trainees.id"), nullable=False),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("physical_activities.id"), nullable=False),
        sa.Column("test_date", sa.Date(), nullable=False),
        sa.Column("raw_value", sa.Numeric(6, 2), nullable=False),
        sa.Column("computed_grade", grade_level, nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_physical_test_results_trainee_id", "physical_test_results", ["trainee_id"])
    op.create_index("ix_physical_test_results_activity_id", "physical_test_results", ["activity_id"])

    op.create_table(
        "training_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trainees.id"), nullable=False),
        sa.Column("subject_name", sa.String(150), nullable=False),
        sa.Column("instructor_name", sa.String(150), nullable=False),
        sa.Column("indoor_outdoor", indoor_outdoor, nullable=False),
        sa.Column("periods_attended", sa.Integer(), server_default="0"),
        sa.Column("periods_total", sa.Integer(), server_default="0"),
        sa.Column("practical_performance", sa.Text(), nullable=True),
        sa.Column("bpet_ppt_performance", sa.Text(), nullable=True),
        sa.Column("drill_performance", sa.Text(), nullable=True),
        sa.Column("pt_performance", sa.Text(), nullable=True),
        sa.Column("weapon_training", sa.Text(), nullable=True),
        sa.Column("firing_practice", sa.Text(), nullable=True),
        sa.Column("obstacle_training", sa.Text(), nullable=True),
        sa.Column("tactical_training", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_training_records_trainee_id", "training_records", ["trainee_id"])

    op.create_table(
        "weekly_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trainees.id"), nullable=False),
        sa.Column("test_date", sa.Date(), nullable=False),
        sa.Column("subject", sa.String(150), nullable=False),
        sa.Column("maximum_marks", sa.Numeric(6, 2), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(6, 2), nullable=False),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("result_status", result_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_weekly_tests_trainee_id", "weekly_tests", ["trainee_id"])

    op.create_table(
        "monthly_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trainees.id"), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("subject_wise_marks", postgresql.JSONB(), nullable=False),
        sa.Column("aggregate", sa.Numeric(7, 2), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_monthly_tests_trainee_id", "monthly_tests", ["trainee_id"])

    op.create_table(
        "quarterly_exams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trainees.id"), nullable=False),
        sa.Column("quarter", sa.String(10), nullable=False),
        sa.Column("written_marks", sa.Numeric(6, 2), nullable=False),
        sa.Column("practical_marks", sa.Numeric(6, 2), nullable=False),
        sa.Column("pt_marks", sa.Numeric(6, 2), nullable=False),
        sa.Column("firing_marks", sa.Numeric(6, 2), nullable=False),
        sa.Column("total_marks", sa.Numeric(7, 2), nullable=False),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_quarterly_exams_trainee_id", "quarterly_exams", ["trainee_id"])

    op.create_table(
        "final_examinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trainee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trainees.id"), nullable=False, unique=True),
        sa.Column("written_examination", sa.Numeric(6, 2), nullable=False),
        sa.Column("practical_examination", sa.Numeric(6, 2), nullable=False),
        sa.Column("pt_test", sa.Numeric(6, 2), nullable=False),
        sa.Column("bpet", sa.Numeric(6, 2), nullable=False),
        sa.Column("ppt", sa.Numeric(6, 2), nullable=False),
        sa.Column("firing_classification", sa.Numeric(6, 2), nullable=False),
        sa.Column("outdoor_assessment", sa.Numeric(6, 2), nullable=False),
        sa.Column("indoor_assessment", sa.Numeric(6, 2), nullable=False),
        sa.Column("field_craft", sa.Numeric(6, 2), nullable=False),
        sa.Column("battle_craft", sa.Numeric(6, 2), nullable=False),
        sa.Column("drill_test", sa.Numeric(6, 2), nullable=False),
        sa.Column("weapon_test", sa.Numeric(6, 2), nullable=False),
        sa.Column("aggregate_marks", sa.Numeric(7, 2), nullable=False),
        sa.Column("final_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("merit_position", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_final_examinations_trainee_id", "final_examinations", ["trainee_id"])


def downgrade() -> None:
    op.drop_table("final_examinations")
    op.drop_table("quarterly_exams")
    op.drop_table("monthly_tests")
    op.drop_table("weekly_tests")
    op.drop_table("training_records")
    op.drop_table("physical_test_results")
    op.drop_table("physical_standards")
    op.drop_table("physical_activities")
    op.drop_table("trainees")
    op.drop_table("batches")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_name in ["indoor_outdoor", "result_status", "grade_level", "comparison_type", "test_category", "user_role"]:
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
