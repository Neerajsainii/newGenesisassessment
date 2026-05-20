from __future__ import annotations

import csv
import heapq
import os
from pathlib import Path
from typing import Iterator

from .config import CHUNK_SIZE, MAX_OPEN_RUNS


def _chunked_rows(
    file_path: Path, key_col: str, chunk_size: int
) -> tuple[list[str], list[list[str]], int]:
    with file_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        key_idx = header.index(key_col)
        chunk: list[list[str]] = []
        for row in reader:
            chunk.append(row)
            if len(chunk) >= chunk_size:
                yield header, chunk, key_idx
                chunk = []
        if chunk:
            yield header, chunk, key_idx


def _sort_and_write_run(
    chunk: list[list[str]], key_idx: int, run_path: Path, header: list[str]
) -> None:
    chunk.sort(key=lambda r: int(r[key_idx]))
    with run_path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(header)
        writer.writerows(chunk)


def _iter_data_rows(path: Path) -> Iterator[list[str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        _ = next(reader)
        for row in reader:
            yield row


def _merge_sorted_runs(run_paths: list[Path], key_idx: int, output_path: Path) -> None:
    file_handles = [p.open("r", newline="", encoding="utf-8") for p in run_paths]
    readers = [csv.reader(h) for h in file_handles]
    header = next(readers[0])
    for r in readers[1:]:
        _ = next(r)

    with output_path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(header)

        heap: list[tuple[int, int, list[str]]] = []
        for i, r in enumerate(readers):
            row = next(r, None)
            if row is not None:
                heap.append((int(row[key_idx]), i, row))
        heapq.heapify(heap)

        while heap:
            _, src, row = heapq.heappop(heap)
            writer.writerow(row)
            nxt = next(readers[src], None)
            if nxt is not None:
                heapq.heappush(heap, (int(nxt[key_idx]), src, nxt))

    for h in file_handles:
        h.close()


def _external_sort(file_path: Path, key_col: str, work_dir: Path) -> Path:
    run_paths: list[Path] = []
    work_dir.mkdir(parents=True, exist_ok=True)

    key_idx = 0
    for i, (header, chunk, key_idx) in enumerate(
        _chunked_rows(file_path, key_col, CHUNK_SIZE), start=1
    ):
        run_path = work_dir / f"{file_path.stem}.run_{i:05d}.csv"
        _sort_and_write_run(chunk, key_idx, run_path, header)
        run_paths.append(run_path)

    if not run_paths:
        raise ValueError(f"No data rows found in {file_path}")

    if len(run_paths) == 1:
        return run_paths[0]

    level = 0
    current_runs = run_paths
    while len(current_runs) > 1:
        level += 1
        merged_runs: list[Path] = []
        for i in range(0, len(current_runs), MAX_OPEN_RUNS):
            group = current_runs[i : i + MAX_OPEN_RUNS]
            out_path = work_dir / f"{file_path.stem}.merged_L{level}_{i//MAX_OPEN_RUNS:05d}.csv"
            _merge_sorted_runs(group, key_idx, out_path)
            merged_runs.append(out_path)
            for rp in group:
                if rp.exists():
                    rp.unlink()
        current_runs = merged_runs

    return current_runs[0]


def _read_group(reader: csv.reader, key_idx: int, first_row: list[str]) -> tuple[int, list[list[str]], list[str] | None]:
    key = int(first_row[key_idx])
    group = [first_row]
    while True:
        row = next(reader, None)
        if row is None:
            return key, group, None
        if int(row[key_idx]) != key:
            return key, group, row
        group.append(row)


def merge_join_sorted_csv(
    users_sorted: Path,
    transactions_sorted: Path,
    output_path: Path,
    users_key_col: str = "user_id",
    tx_key_col: str = "user_id",
) -> int:
    rows_written = 0
    with users_sorted.open("r", newline="", encoding="utf-8") as uf, transactions_sorted.open(
        "r", newline="", encoding="utf-8"
    ) as tf, output_path.open("w", newline="", encoding="utf-8") as out:
        ur = csv.reader(uf)
        tr = csv.reader(tf)
        uw = next(ur)
        tw = next(tr)
        u_key_idx = uw.index(users_key_col)
        t_key_idx = tw.index(tx_key_col)

        merged_header = ["transaction_id", "user_id", "amount", "name", "signup_date"]
        writer = csv.writer(out)
        writer.writerow(merged_header)

        u_row = next(ur, None)
        t_row = next(tr, None)
        while u_row is not None and t_row is not None:
            u_key = int(u_row[u_key_idx])
            t_key = int(t_row[t_key_idx])
            if u_key < t_key:
                u_row = next(ur, None)
            elif u_key > t_key:
                t_row = next(tr, None)
            else:
                _, u_group, next_u = _read_group(ur, u_key_idx, u_row)
                _, t_group, next_t = _read_group(tr, t_key_idx, t_row)
                for tx in t_group:
                    for user in u_group:
                        writer.writerow([tx[0], tx[1], tx[2], user[1], user[2]])
                        rows_written += 1
                u_row = next_u
                t_row = next_t
    return rows_written


def run_out_of_core_join(
    users_csv_path: Path,
    transactions_csv_path: Path,
    output_csv_path: Path,
    tmp_root: Path,
    job_id: str,
) -> int:
    job_tmp_dir = tmp_root / job_id
    users_work = job_tmp_dir / "users_sort"
    tx_work = job_tmp_dir / "tx_sort"
    job_tmp_dir.mkdir(parents=True, exist_ok=True)

    users_sorted = _external_sort(users_csv_path, "user_id", users_work)
    tx_sorted = _external_sort(transactions_csv_path, "user_id", tx_work)

    temp_output = output_csv_path.with_suffix(".tmp")
    rows_written = merge_join_sorted_csv(users_sorted, tx_sorted, temp_output)
    temp_output.replace(output_csv_path)

    return rows_written

