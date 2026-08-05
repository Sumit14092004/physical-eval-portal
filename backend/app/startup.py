"""
Runs automatically when the app boots (see main.py). Handles the two
things a genuinely fresh database needs before anyone can use the
portal, without requiring Shell access (not available on Render's free
tier):

1. Physical standards reference data (BPET/PPT tables) -- real official
   data, not a demo fixture, and there's no admin UI for entering ~30
   threshold rows by hand, so this is seeded here instead.
2. Exactly one bootstrap admin account, so someone can log into the
   Admin screens at all on a brand new deployment. Real batches and
   trainees are expected to be entered through the Admin UI afterward,
   not auto-seeded -- unlike app/db/seed_demo_data.py (which is for
   local/demo use only and is never called from here).

Both steps check first and skip if data already exists, so this is safe
to run on every single boot (every deploy, every free-tier cold start)
without ever creating duplicates or extra admin accounts.
"""
from sqlalchemy import select, func

from app.db.base import AsyncSessionLocal
from app.models.physical_evaluation import PhysicalActivity
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import hash_password
from app.db.seed_physical_standards import (
    BPET_ACTIVITIES, PPT_ACTIVITIES, BPET_STANDARDS, PPT_STANDARDS,
    PERSONNEL_CATEGORY,
)
from app.models.physical_evaluation import PhysicalStandard
from app.models.enums import TestCategory

BOOTSTRAP_ADMIN_EMAIL = "admin@academy.local"
BOOTSTRAP_ADMIN_PASSWORD = "Academy@2026"


async def seed_physical_standards_if_empty() -> None:
    async with AsyncSessionLocal() as db:
        count = (await db.execute(select(func.count()).select_from(PhysicalActivity))).scalar()
        if count and count > 0:
            return

        activity_lookup = {}
        for name, unit, comparison in BPET_ACTIVITIES:
            activity = PhysicalActivity(test_category=TestCategory.BPET, name=name, unit=unit, comparison_type=comparison)
            db.add(activity)
            activity_lookup[("bpet", name)] = activity
        for name, unit, comparison in PPT_ACTIVITIES:
            activity = PhysicalActivity(test_category=TestCategory.PPT, name=name, unit=unit, comparison_type=comparison)
            db.add(activity)
            activity_lookup[("ppt", name)] = activity
        await db.flush()

        for name, bands in BPET_STANDARDS.items():
            activity = activity_lookup[("bpet", name)]
            for (age_min, age_max), (ex, good, sat) in bands.items():
                db.add(PhysicalStandard(
                    activity_id=activity.id, personnel_category=PERSONNEL_CATEGORY,
                    age_min=age_min, age_max=age_max,
                    excellent_value=ex, good_value=good, satisfactory_value=sat,
                ))
        for name, bands in PPT_STANDARDS.items():
            activity = activity_lookup[("ppt", name)]
            for (age_min, age_max), (ex, good, sat) in bands.items():
                db.add(PhysicalStandard(
                    activity_id=activity.id, personnel_category=PERSONNEL_CATEGORY,
                    age_min=age_min, age_max=age_max,
                    excellent_value=ex, good_value=good, satisfactory_value=sat,
                ))
        await db.commit()
        print("[startup] Seeded physical standards.")


async def create_bootstrap_admin_if_none() -> None:
    async with AsyncSessionLocal() as db:
        count = (await db.execute(select(func.count()).select_from(User))).scalar()
        if count and count > 0:
            return

        db.add(User(
            email=BOOTSTRAP_ADMIN_EMAIL,
            hashed_password=hash_password(BOOTSTRAP_ADMIN_PASSWORD),
            full_name="Bootstrap Admin",
            role=UserRole.ADMIN,
        ))
        await db.commit()
        print(f"[startup] Created bootstrap admin: {BOOTSTRAP_ADMIN_EMAIL}")


async def run_startup_tasks() -> None:
    await seed_physical_standards_if_empty()
    await create_bootstrap_admin_if_none()
