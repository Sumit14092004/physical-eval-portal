from celery import shared_task
from sqlalchemy import text
from app.db.sync_base import SyncSessionLocal
from app.services import ranking_sync


@shared_task(name="tasks.recompute_final_exam_ranks", bind=True, max_retries=3, default_retry_delay=5)
def recompute_final_exam_ranks_task(self, batch_id: str):
    db = SyncSessionLocal()
    try:
        ranking_sync.recompute_final_exam_ranks_sync(db, batch_id)
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(name="tasks.recompute_monthly_ranks", bind=True, max_retries=3, default_retry_delay=5)
def recompute_monthly_ranks_task(self, batch_id: str, month: str):
    db = SyncSessionLocal()
    try:
        ranking_sync.recompute_monthly_ranks_sync(db, batch_id, month)
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(name="tasks.recompute_quarterly_ranks", bind=True, max_retries=3, default_retry_delay=5)
def recompute_quarterly_ranks_task(self, batch_id: str, quarter: str):
    db = SyncSessionLocal()
    try:
        ranking_sync.recompute_quarterly_ranks_sync(db, batch_id, quarter)
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(name="tasks.reconcile_all_ranks")
def reconcile_all_ranks_task():
    """
    Periodic safety net (see celery_app.py beat_schedule): rank
    recomputation is normally triggered per-submission, which is fast
    but event-driven -- if a task is ever dropped (worker restart mid-job,
    a transient failure that exhausts its retries, etc.) a batch's ranks
    could quietly go stale. This walks every (batch, period) combination
    that actually has data and recomputes ranks for all of them, so
    staleness self-heals within one beat interval rather than needing
    someone to notice and manually trigger a fix.
    """
    db = SyncSessionLocal()
    try:
        batch_ids = [
            str(r[0]) for r in db.execute(text("SELECT id FROM batches")).fetchall()
        ]
        for batch_id in batch_ids:
            ranking_sync.recompute_final_exam_ranks_sync(db, batch_id)

            months = db.execute(
                text("""
                    SELECT DISTINCT mt.month FROM monthly_tests mt
                    JOIN trainees t ON t.id = mt.trainee_id
                    WHERE t.batch_id = :batch_id
                """),
                {"batch_id": batch_id},
            ).fetchall()
            for (month,) in months:
                ranking_sync.recompute_monthly_ranks_sync(db, batch_id, str(month))

            quarters = db.execute(
                text("""
                    SELECT DISTINCT qe.quarter FROM quarterly_exams qe
                    JOIN trainees t ON t.id = qe.trainee_id
                    WHERE t.batch_id = :batch_id
                """),
                {"batch_id": batch_id},
            ).fetchall()
            for (quarter,) in quarters:
                ranking_sync.recompute_quarterly_ranks_sync(db, batch_id, quarter)
    finally:
        db.close()
