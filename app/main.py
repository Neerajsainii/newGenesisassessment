from __future__ import annotations

from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from .config import JOBS_DB_PATH
from .job_store import JobStore
from .logging_config import configure_logging
from .service import process_join_job
from .tasks import run_join_task


configure_logging()
app = FastAPI(title="Scalable Data Processing API")
job_store = JobStore(JOBS_DB_PATH)


class TriggerResponse(BaseModel):
    job_id: str
    status: str
    mode: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/trigger-join/background", response_model=TriggerResponse, status_code=202)
def trigger_join_background(background_tasks: BackgroundTasks) -> TriggerResponse:
    job_id = str(uuid4())
    job_store.create_job(job_id, mode="background_tasks")
    background_tasks.add_task(process_join_job, job_id, job_store)
    return TriggerResponse(job_id=job_id, status="queued", mode="background_tasks")


@app.post("/trigger-join/celery", response_model=TriggerResponse, status_code=202)
def trigger_join_celery() -> TriggerResponse:
    job_id = str(uuid4())
    job_store.create_job(job_id, mode="celery")
    run_join_task.delay(job_id)
    return TriggerResponse(job_id=job_id, status="queued", mode="celery")


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str) -> dict:
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job

