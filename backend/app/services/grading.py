"""
Grading engine for BPET/PPT physical evaluation.

Design goal: the actual Ex/Good/Sat numbers (from the official tables)
live entirely in the `physical_standards` DB table, not in this code.
This function only encodes the *comparison logic*, which is stable
even if numeric standards are revised. That separation is what lets
an admin update thresholds (new circular, new age band, new personnel
category) without a code deploy.
"""
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.physical_evaluation import PhysicalActivity, PhysicalStandard
from app.models.enums import ComparisonType, GradeLevel


def compute_age(date_of_birth: date, as_of: date | None = None) -> int:
    as_of = as_of or date.today()
    years = as_of.year - date_of_birth.year
    if (as_of.month, as_of.day) < (date_of_birth.month, date_of_birth.day):
        years -= 1
    return years


async def get_applicable_standard(
    db: AsyncSession,
    activity_id,
    age: int,
    personnel_category: str = "GD Personnel",
) -> PhysicalStandard | None:
    stmt = select(PhysicalStandard).where(
        PhysicalStandard.activity_id == activity_id,
        PhysicalStandard.personnel_category == personnel_category,
        PhysicalStandard.age_min <= age,
        PhysicalStandard.age_max >= age,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def grade_from_thresholds(
    raw_value: float,
    comparison_type: ComparisonType,
    excellent: float | None,
    good: float | None,
    satisfactory: float | None,
) -> GradeLevel:
    """
    Pure function, unit-testable in isolation from the DB.

    LOWER_IS_BETTER (race times): raw_value <= excellent -> EXCELLENT, etc.
    HIGHER_IS_BETTER (rope height, chin-ups): raw_value >= excellent -> EXCELLENT, etc.
    """
    if comparison_type == ComparisonType.LOWER_IS_BETTER:
        if excellent is not None and raw_value <= excellent:
            return GradeLevel.EXCELLENT
        if good is not None and raw_value <= good:
            return GradeLevel.GOOD
        if satisfactory is not None and raw_value <= satisfactory:
            return GradeLevel.SATISFACTORY
        return GradeLevel.FAIL
    else:  # HIGHER_IS_BETTER
        if excellent is not None and raw_value >= excellent:
            return GradeLevel.EXCELLENT
        if good is not None and raw_value >= good:
            return GradeLevel.GOOD
        if satisfactory is not None and raw_value >= satisfactory:
            return GradeLevel.SATISFACTORY
        return GradeLevel.FAIL


async def grade_result(
    db: AsyncSession,
    activity: PhysicalActivity,
    raw_value: float,
    trainee_date_of_birth: date,
    personnel_category: str = "GD Personnel",
    test_date: date | None = None,
) -> GradeLevel | None:
    age = compute_age(trainee_date_of_birth, test_date)
    standard = await get_applicable_standard(db, activity.id, age, personnel_category)
    if standard is None:
        # No standard defined for this age band + activity (e.g. "Toe touch"
        # is marked "-" for 30-40 in the source table) -> not applicable.
        return None
    return grade_from_thresholds(
        raw_value,
        activity.comparison_type,
        float(standard.excellent_value) if standard.excellent_value is not None else None,
        float(standard.good_value) if standard.good_value is not None else None,
        float(standard.satisfactory_value) if standard.satisfactory_value is not None else None,
    )
