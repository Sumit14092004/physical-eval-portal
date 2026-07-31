"""
Rank computation for Monthly/Quarterly/Final results.

At 150k+ trainees, computing rank in Python (pull all rows, sort,
enumerate) is the wrong approach -- it's O(n log n) in app memory per
request and doesn't scale past a single batch comfortably. Instead we
push ranking into Postgres using RANK() OVER (...), which is set-based,
index-friendly, and lets the DB do what it's good at.

These run as Celery background jobs after marks entry closes for a
given batch/period, not synchronously on every mark submission.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def recompute_final_exam_ranks(db: AsyncSession, batch_id: str) -> None:
    stmt = text("""
        WITH ranked AS (
            SELECT
                fe.id,
                RANK() OVER (ORDER BY fe.aggregate_marks DESC) AS new_rank
            FROM final_examinations fe
            JOIN trainees t ON t.id = fe.trainee_id
            WHERE t.batch_id = :batch_id
        )
        UPDATE final_examinations fe
        SET merit_position = ranked.new_rank
        FROM ranked
        WHERE fe.id = ranked.id
    """)
    await db.execute(stmt, {"batch_id": batch_id})
    await db.commit()


async def recompute_monthly_ranks(db: AsyncSession, batch_id: str, month: str) -> None:
    stmt = text("""
        WITH ranked AS (
            SELECT
                mt.id,
                RANK() OVER (ORDER BY mt.aggregate DESC) AS new_rank
            FROM monthly_tests mt
            JOIN trainees t ON t.id = mt.trainee_id
            WHERE t.batch_id = :batch_id AND mt.month = :month
        )
        UPDATE monthly_tests mt
        SET rank = ranked.new_rank
        FROM ranked
        WHERE mt.id = ranked.id
    """)
    await db.execute(stmt, {"batch_id": batch_id, "month": month})
    await db.commit()


async def recompute_quarterly_ranks(db: AsyncSession, batch_id: str, quarter: str) -> None:
    stmt = text("""
        WITH ranked AS (
            SELECT
                qe.id,
                RANK() OVER (ORDER BY qe.total_marks DESC) AS new_rank
            FROM quarterly_exams qe
            JOIN trainees t ON t.id = qe.trainee_id
            WHERE t.batch_id = :batch_id AND qe.quarter = :quarter
        )
        UPDATE quarterly_exams qe
        SET rank = ranked.new_rank
        FROM ranked
        WHERE qe.id = ranked.id
    """)
    await db.execute(stmt, {"batch_id": batch_id, "quarter": quarter})
    await db.commit()
