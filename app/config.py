from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
RESULT_DIR = Path(os.getenv("RESULT_DIR", BASE_DIR / "results"))
TMP_DIR = Path(os.getenv("TMP_DIR", BASE_DIR / "tmp"))

JOBS_DB_PATH = Path(os.getenv("JOBS_DB_PATH", BASE_DIR / "jobs.db"))

USERS_CSV_PATH = Path(os.getenv("USERS_CSV_PATH", DATA_DIR / "users.csv"))
TRANSACTIONS_CSV_PATH = Path(
    os.getenv("TRANSACTIONS_CSV_PATH", DATA_DIR / "transactions.csv")
)

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "50000"))
MAX_OPEN_RUNS = int(os.getenv("MAX_OPEN_RUNS", "64"))

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

