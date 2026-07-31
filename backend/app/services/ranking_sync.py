"""
Sync mirror of app/services/ranking.py, for use inside Celery tasks
where there's no event loop. Same SQL, same logic -- kept as a
near-duplicate rather than a shared abstraction because the async/sync
session APIs differ enough that a shared wrapper would add more
indirection than it saves for three queries this size. If a fourth or
fifth ranking query gets added, revisit and factor out the shared SQL
strings.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def recompute_final_exam_ranks_sync(db: Session, batch_id: str) -> None:
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
    db.execute(stmt, {"batch_id": batch_id})
    db.commit()


def recompute_monthly_ranks_sync(db: Session, batch_id: str, month: str) -> None:
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
    db.execute(stmt, {"batch_id": batch_id, "month": month})
    db.commit()


def recompute_quarterly_ranks_sync(db: Session, batch_id: str, quarter: str) -> None:
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
    db.execute(stmt, {"batch_id": batch_id, "quarter": quarter})
    db.commit()
