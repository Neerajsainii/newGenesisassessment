# Scalable Data Processing API

Implements both assignment parts:
- Out-of-core inner join for large CSVs using external sort + streaming merge join.
- FastAPI endpoint that triggers join jobs asynchronously.
- Two non-blocking approaches:
  - FastAPI `BackgroundTasks`
  - Celery worker queue

## Assignment Requirements Mapping

- Assignment 1 (Out-of-core join):
  - Implemented in `app/join_engine.py` using external sort + streaming merge join.
  - Does not load full CSV files into memory.
- Assignment 2 (Non-blocking API):
  - `POST /trigger-join/background` and `POST /trigger-join/celery` return immediately with `job_id`.
  - Join runs asynchronously in background.
  - Start/finish logging implemented in `app/service.py`.
  - Job status is tracked in SQLite (`jobs.db`) and exposed by `GET /jobs/{job_id}`.

## Project Structure

```text
app/
  main.py          # FastAPI app
  join_engine.py   # External sort + merge join
  service.py       # Job execution logic
  tasks.py         # Celery task wrapper
  job_store.py     # SQLite job metadata
  config.py        # Paths and runtime config
```

## Approach 1: FastAPI BackgroundTasks

Type:
- In-process asynchronous background execution (same FastAPI process).

Step-by-step flow:
1. Client calls `POST /trigger-join/background`.
2. API creates `job_id` with status `queued`.
3. API returns `202 Accepted` + `job_id` immediately.
4. FastAPI schedules `process_join_job(job_id)` in `BackgroundTasks`.
5. Task marks job `running`, executes out-of-core join, writes `result_<job_id>.csv`.
6. Task marks job `succeeded`/`failed` and logs completion/failure.

Pros:
- Simple and quick to implement.
- No extra infrastructure required.
- Good for demos and low load.

Cons:
- Heavy jobs share API process resources (CPU/RAM).
- Job can be lost on API process restart/crash.
- Limited scalability for many concurrent long jobs.

## Approach 2: Celery Worker Queue

Type:
- Queue-based distributed background processing (separate worker process).

Step-by-step flow:
1. Client calls `POST /trigger-join/celery`.
2. API creates `job_id` with status `queued`.
3. API enqueues task (`run_join_task.delay(job_id)`) to Redis broker.
4. API returns `202 Accepted` + `job_id` immediately.
5. Celery worker picks job from queue and runs same join pipeline.
6. Worker marks job `running`, then `succeeded`/`failed`, with logs.

Pros:
- Better isolation from API process.
- Better reliability and scalability.
- Supports queueing/retries and horizontal worker scaling.

Cons:
- Requires Redis + Celery worker setup.
- More operational complexity than BackgroundTasks.

## Why Two Approaches

- BackgroundTasks shows minimal non-blocking implementation.
- Celery shows production-grade non-blocking architecture.
- Both satisfy assignment request to implement at least 2 approaches with pros/cons.

## Install

```bash
pip install -r requirements.txt
```

## Generate Sample Data

```bash
python generate_data.py
```

Place real files at:
- `data/users.csv`
- `data/transactions.csv`

Or override via env:
- `USERS_CSV_PATH`
- `TRANSACTIONS_CSV_PATH`

## Run API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Trigger BackgroundTasks mode

```bash
curl -X POST http://localhost:8000/trigger-join/background
```

### Trigger Celery mode

```bash
curl -X POST http://localhost:8000/trigger-join/celery
```

### Check Job

```bash
curl http://localhost:8000/jobs/<job_id>
```

PowerShell equivalent:
```powershell
$resp = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/trigger-join/background"
$jobId = $resp.job_id
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/jobs/$jobId"
```

## Run Celery Worker

Requires Redis (default `redis://localhost:6379/0`).

```bash
celery -A app.tasks worker --loglevel=info
```

## Notes

- Output path: `results/result_<job_id>.csv`
- Temporary sort files: `tmp/<job_id>/...`
- Job metadata: `jobs.db`
- Main memory-safe join implementation: `app/join_engine.py`
