from __future__ import annotations

import logging
import traceback
from pathlib import Path

from .config import RESULT_DIR, TMP_DIR, TRANSACTIONS_CSV_PATH, USERS_CSV_PATH
from .join_engine import run_out_of_core_join
from .job_store import JobStore
from .logging_config import JobLoggerAdapter


def process_join_job(job_id: str, job_store: JobStore) -> None:
    logger = JobLoggerAdapter(logging.getLogger("join_service"), {"job_id": job_id})
    result_path = RESULT_DIR / f"result_{job_id}.csv"
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        logger.info("Join job started")
        job_store.update_status(job_id, "running")
        rows = run_out_of_core_join(
            users_csv_path=Path(USERS_CSV_PATH),
            transactions_csv_path=Path(TRANSACTIONS_CSV_PATH),
            output_csv_path=result_path,
            tmp_root=TMP_DIR,
            job_id=job_id,
        )
        job_store.update_status(job_id, "succeeded", output_path=str(result_path))
        logger.info("Join job finished successfully. rows_written=%s", rows)
    except Exception:
        err = traceback.format_exc(limit=8)
        job_store.update_status(job_id, "failed", error_message=err)
        logger.error("Join job failed\n%s", err)
        raise

