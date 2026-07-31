"""
Celery workers run synchronous code, while the FastAPI app is fully
async -- so tasks get their own sync engine/session rather than trying
to run an event loop inside a worker. Same database, different driver
(psycopg2 instead of asyncpg).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SYNC_DATABASE_URL = os.getenv(
    "SYNC_DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/physical_eval_portal",
    ).replace("postgresql+asyncpg://", "postgresql+psycopg2://"),
)

sync_engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SyncSessionLocal = sessionmaker(bind=sync_engine)
