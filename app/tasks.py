from .celery_app import celery_app
from .config import JOBS_DB_PATH
from .job_store import JobStore
from .service import process_join_job


@celery_app.task(name="join_task")
def run_join_task(job_id: str) -> None:
    store = JobStore(JOBS_DB_PATH)
    process_join_job(job_id, store)

