import csv
import random
from pathlib import Path


def generate_data(
    out_dir: Path,
    num_users: int = 100_000,
    num_transactions: int = 200_000,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    users_path = out_dir / "users.csv"
    tx_path = out_dir / "transactions.csv"

    with users_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "name", "signup_date"])
        for i in range(1, num_users + 1):
            w.writerow([i, f"User_{i}", f"2020-01-{(i % 28) + 1:02d}"])

    with tx_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["transaction_id", "user_id", "amount"])
        for i in range(1, num_transactions + 1):
            uid = random.randint(1, num_users)
            amt = round(random.uniform(5.0, 500.0), 2)
            w.writerow([i, uid, amt])

    print(f"Generated: {users_path}")
    print(f"Generated: {tx_path}")


if __name__ == "__main__":
    generate_data(Path("data"))

