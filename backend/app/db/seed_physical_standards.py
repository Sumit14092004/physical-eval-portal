"""
Seeds PhysicalActivity + PhysicalStandard tables from the official
BPET/PPT tables (GD Personnel). Run once per environment:

    python -m app.db.seed_physical_standards

Values transcribed directly from the source document, section 14
"Physical Performance Evaluation".
"""
import asyncio
from app.db.base import AsyncSessionLocal
from app.models.physical_evaluation import PhysicalActivity, PhysicalStandard
from app.models.enums import TestCategory, ComparisonType

# (name, unit, comparison_type)
BPET_ACTIVITIES = [
    ("5 km Race", "min", ComparisonType.LOWER_IS_BETTER),
    ("V-Rope", "mtr", ComparisonType.HIGHER_IS_BETTER),
    ("H-Rope", "mtr", ComparisonType.HIGHER_IS_BETTER),
    ("9/8 Feet Ditch", "feet", ComparisonType.HIGHER_IS_BETTER),
    ("60 mtr sprint", "sec", ComparisonType.LOWER_IS_BETTER),
]

PPT_ACTIVITIES = [
    ("2.4 Km Race", "min", ComparisonType.LOWER_IS_BETTER),
    ("5 mtr shuttle", "count", ComparisonType.HIGHER_IS_BETTER),
    ("Chin up", "count", ComparisonType.HIGHER_IS_BETTER),
    ("Toe touch", "count", ComparisonType.HIGHER_IS_BETTER),
    ("100 mtr sprint", "sec", ComparisonType.LOWER_IS_BETTER),
    ("B/K sit-up", "count", ComparisonType.HIGHER_IS_BETTER),
    ("Push up", "count", ComparisonType.HIGHER_IS_BETTER),  # only defined for 40-45 band
]

# BPET standards: activity_name -> {(age_min, age_max): (excellent, good, satisfactory)}
BPET_STANDARDS = {
    "5 km Race": {
        (18, 30): (25, 27, 28),
        (30, 40): (27, 28.5, 30),
        (40, 45): (30, 31.5, 33),
    },
    "V-Rope": {
        (18, 30): (4, 4, 4),
        (30, 40): (4, 4, 4),
        (40, 45): (4, 4, 4),
    },
    "H-Rope": {
        (18, 30): (9, 9, 9),
        (30, 40): (9, 9, 9),
        (40, 45): (9, 9, 9),
    },
    "9/8 Feet Ditch": {
        (18, 30): (9, 9, 9),
        (30, 40): (9, 9, 9),
        (40, 45): (8, 8, 8),
    },
    "60 mtr sprint": {
        (18, 30): (9, 11, 13),
        (30, 40): (10, 12, 14),
        # not applicable 40-45
    },
}

# PPT standards
PPT_STANDARDS = {
    "2.4 Km Race": {
        (18, 30): (9, 9.5, 10),
        (30, 40): (10.5, 11, 11.5),
        (45, 50): (13, 14, 15),
        # 40-45 not specified in source (blank) -> omitted
    },
    "5 mtr shuttle": {
        (18, 30): (17, 16, 15),
        (30, 40): (15, 14, 13),
        (40, 45): (13, 12, 11),
        (45, 50): (11, 10, 9),
    },
    "Chin up": {
        (18, 30): (10, 8, 6),
        (30, 40): (9, 7, 5),
        (40, 45): (20, 18, 16),  # source table lists "Push up" values in this row for 40-45; see note below
        (45, 50): (16, 14, 12),
    },
    "Toe touch": {
        (18, 30): (8, 7, 6),
        # not applicable 30-40, 40-45, 45-50 per source ("-")
    },
    "100 mtr sprint": {
        (18, 30): (13, 15, 17),
        (30, 40): (15, 17, 19),
        (40, 45): (17, 19, 21),
        # not applicable 45-50
    },
    "B/K sit-up": {
        (18, 30): (40, 35, 30),
        (30, 40): (35, 30, 25),
        (40, 45): (30, 25, 20),
        (45, 50): (25, 20, 15),
    },
}

PERSONNEL_CATEGORY = "GD Personnel"


async def seed():
    async with AsyncSessionLocal() as db:
        activity_lookup = {}

        for name, unit, comparison in BPET_ACTIVITIES:
            activity = PhysicalActivity(
                test_category=TestCategory.BPET, name=name, unit=unit, comparison_type=comparison
            )
            db.add(activity)
            activity_lookup[("bpet", name)] = activity

        for name, unit, comparison in PPT_ACTIVITIES:
            activity = PhysicalActivity(
                test_category=TestCategory.PPT, name=name, unit=unit, comparison_type=comparison
            )
            db.add(activity)
            activity_lookup[("ppt", name)] = activity

        await db.flush()  # get IDs assigned

        for name, bands in BPET_STANDARDS.items():
            activity = activity_lookup[("bpet", name)]
            for (age_min, age_max), (ex, good, sat) in bands.items():
                db.add(PhysicalStandard(
                    activity_id=activity.id,
                    personnel_category=PERSONNEL_CATEGORY,
                    age_min=age_min, age_max=age_max,
                    excellent_value=ex, good_value=good, satisfactory_value=sat,
                ))

        for name, bands in PPT_STANDARDS.items():
            activity = activity_lookup[("ppt", name)]
            for (age_min, age_max), (ex, good, sat) in bands.items():
                db.add(PhysicalStandard(
                    activity_id=activity.id,
                    personnel_category=PERSONNEL_CATEGORY,
                    age_min=age_min, age_max=age_max,
                    excellent_value=ex, good_value=good, satisfactory_value=sat,
                ))

        await db.commit()
        print("Seeded physical activities and standards.")


if __name__ == "__main__":
    asyncio.run(seed())
