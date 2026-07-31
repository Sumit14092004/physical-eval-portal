"""
Seeds base demo data: 5 staff accounts (mix of admin/instructor) + one
batch + 50 trainees spread across age bands so BPET/PPT grading can be
exercised against every threshold row in physical_standards.

Run after seed_physical_standards.py:

    python -m app.db.seed_demo_data

All accounts share the password below -- change it after first login
in anything beyond a local demo.
"""
import asyncio
import random
from datetime import date

from app.db.base import AsyncSessionLocal
from app.models.user import User, Batch, Trainee
from app.models.enums import UserRole
from app.core.security import hash_password

DEMO_PASSWORD = "Academy@2026"

# 5 staff accounts: trainer (instructor) + you + three others (admins),
# per what was asked for.
STAFF_ACCOUNTS = [
    {"email": "trainer@academy.test", "full_name": "Ramesh Yadav", "role": UserRole.INSTRUCTOR},
    {"email": "sumit.admin@academy.test", "full_name": "Sumit (Admin)", "role": UserRole.ADMIN},
    {"email": "admin2@academy.test", "full_name": "Priya Nair", "role": UserRole.ADMIN},
    {"email": "admin3@academy.test", "full_name": "Arjun Mehta", "role": UserRole.ADMIN},
    {"email": "admin4@academy.test", "full_name": "Kavita Rao", "role": UserRole.ADMIN},
]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
    "Ishaan", "Rohan", "Kabir", "Aryan", "Devansh", "Yash", "Karan", "Nikhil",
    "Manish", "Rahul", "Vikram", "Ankit", "Suresh", "Ramesh", "Deepak", "Ajay",
    "Sanjay", "Rakesh", "Amit", "Vijay", "Anil", "Sunil",
    "Priya", "Ananya", "Diya", "Saanvi", "Aadhya", "Kavya", "Ishita", "Riya",
    "Neha", "Pooja", "Anjali", "Sneha", "Divya", "Meera", "Swati", "Nisha",
    "Rekha", "Sarita", "Kirti", "Bhavna",
]

LAST_NAMES = [
    "Sharma", "Verma", "Yadav", "Singh", "Kumar", "Gupta", "Mishra", "Tiwari",
    "Chauhan", "Rathore", "Patel", "Nair", "Reddy", "Rao", "Iyer", "Menon",
    "Joshi", "Desai", "Pandey", "Dubey", "Thakur", "Bhatt", "Naik", "Shetty",
]

GENDERS = ["Male", "Female"]

# Weighted toward the 18-30 GD-recruit band (typical for a fresh training
# batch), with a handful of older personnel to exercise the other age-band
# standards during grading.
AGE_BAND_WEIGHTS = [
    ((18, 30), 38),
    ((30, 40), 8),
    ((40, 45), 3),
    ((45, 50), 1),
]


def random_dob_for_band(age_min: int, age_max: int, as_of: date) -> date:
    age = random.randint(age_min, age_max)
    # random day within the birth year to avoid every DOB landing on Jan 1
    birth_year = as_of.year - age
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(birth_year, month, day)


async def seed():
    async with AsyncSessionLocal() as db:
        # --- staff accounts ---
        for acct in STAFF_ACCOUNTS:
            user = User(
                email=acct["email"],
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name=acct["full_name"],
                role=acct["role"],
            )
            db.add(user)

        # --- batch ---
        batch = Batch(
            name="GD Constable Batch 2026-A",
            start_date=date(2026, 7, 1),
            end_date=date(2027, 3, 31),
        )
        db.add(batch)
        await db.flush()  # get batch.id

        # --- 50 trainees ---
        as_of = date.today()
        band_pool = []
        for band, count in AGE_BAND_WEIGHTS:
            band_pool.extend([band] * count)
        random.shuffle(band_pool)

        used_names = set()
        for i in range(1, 51):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            while (first, last) in used_names:
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
            used_names.add((first, last))
            full_name = f"{first} {last}"

            enrollment_number = f"GD2026A{i:03d}"
            email = f"trainee{i:03d}@academy.test"
            age_band = band_pool[i - 1]
            dob = random_dob_for_band(age_band[0], age_band[1], as_of)
            gender = random.choice(GENDERS)

            user = User(
                email=email,
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name=full_name,
                role=UserRole.TRAINEE,
            )
            db.add(user)
            await db.flush()

            trainee = Trainee(
                user_id=user.id,
                batch_id=batch.id,
                enrollment_number=enrollment_number,
                date_of_birth=dob,
                gender=gender,
                personnel_category="GD Personnel",
            )
            db.add(trainee)

        await db.commit()
        print(f"Seeded {len(STAFF_ACCOUNTS)} staff accounts, 1 batch, 50 trainees.")
        print(f"All demo accounts use password: {DEMO_PASSWORD}")
        print("Staff logins:")
        for acct in STAFF_ACCOUNTS:
            print(f"  {acct['email']}  ({acct['role'].value})")


if __name__ == "__main__":
    asyncio.run(seed())
