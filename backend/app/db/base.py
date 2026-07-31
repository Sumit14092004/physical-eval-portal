"""
Database engine + session setup.

Using SQLAlchemy 2.0 style with async support so the API can handle
high concurrency (target scale: 150,000+ trainees, many concurrent
instructors entering marks during exam windows).
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/physical_eval_portal",
)

# pool_size/max_overflow tuned conservatively for a single instance to start;
# bump these (and move to PgBouncer) as instructor concurrency grows.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
