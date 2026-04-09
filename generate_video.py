"""
Batch render video từ thư mục JSON; có thể chạy đa tiến trình (Windows spawn).

Chỉ song song hóa lời gọi ``generate_video`` — mỗi process tự import model một lần.
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

from dotenv import load_dotenv
from tqdm import tqdm

from src.generate_video_worker import run_generate_video_job


def _collect_json_paths(folder: str) -> list[str]:
    """Giống ``os.listdir(folder)`` + chỉ lấy ``.json``, sắp xếp ổn định."""
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Không thấy thư mục: {os.path.abspath(folder)}")
    names = sorted(
        f for f in os.listdir(folder) if f.lower().endswith(".json")
    )
    return [os.path.join(folder, f) for f in names]


def main() -> None:
    """Parse CLI và chạy tuần tự hoặc đa process."""
    load_dotenv()
    parser = argparse.ArgumentParser(description="Render podcast video từ JSON trong thư mục.")
    parser.add_argument(
        "--folder",
        default="save/script/",
        help="Thư mục chứa file {student_id}_{month}.json",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1 ,
        help="Số process (0 = số CPU; 1 = tuần tự)",
    )
    args = parser.parse_args()

    paths = _collect_json_paths(args.folder)
    if not paths:
        print("Không có file .json nào.", file=sys.stderr)
        sys.exit(1)

    n_workers = args.workers
    if n_workers <= 0:
        n_workers = max(1, (os.cpu_count() or 2))

    str_paths = [os.path.abspath(p) for p in paths]

    if n_workers == 1:
        errors: list[tuple[str, str]] = []
        for p in tqdm(str_paths, desc="generate_video"):
            path_s, err = run_generate_video_job(p)
            if err:
                errors.append((path_s, err))
    else:
        errors = []
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            futures = {
                ex.submit(run_generate_video_job, p): p for p in str_paths
            }
            for fut in tqdm(
                as_completed(futures),
                total=len(futures),
                desc=f"generate_video ({n_workers} workers)",
            ):
                path_s, err = fut.result()
                if err:
                    errors.append((path_s, err))

    if errors:
        print(f"\nHoàn tất với {len(errors)} lỗi:", file=sys.stderr)
        for path_s, err in errors:
            print(f"  {path_s}: {err}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {len(paths)} file.")


if __name__ == "__main__":
    main()
