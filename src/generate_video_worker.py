"""
Worker chạy trong process con: gọi ``generate_video`` cho một file JSON kịch bản.

Tách riêng module để Windows (``spawn``) pickle được hàm worker.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_generate_video_job(json_path: str) -> tuple[str, str | None]:
    """
    Đọc một file ``save/script/{id}_{month}.json`` và render video.

    Parameters
    ----------
    json_path:
        Đường dẫn tuyệt đối hoặc tương đối tới file JSON.

    Returns
    -------
    tuple[str, str | None]
        ``(đường_dẫn, None)`` nếu thành công; ``(đường_dẫn, thông_báo_lỗi)`` nếu lỗi.
    """
    from dotenv import load_dotenv

    from src.core import generate_video

    load_dotenv()
    path = Path(json_path)
    try:
        # Giống logic cũ: ``file.split("_")[0]`` và ``file.split("_")[1].split(".")[0]``
        file = path.name
        parts = file.split("_")
        if len(parts) < 2:
            return str(path), f"Tên file cần có ít nhất một '_': {file}"
        student_id = parts[0]
        month = parts[1].split(".")[0]

        with path.open("r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        result = data.get("result")
        if not isinstance(result, dict):
            return str(path), "Thiếu hoặc sai kiểu key 'result'"

        highlight = data.get("highlight")
        improve_list = data.get("improve_list")
        if improve_list is None:
            improve_list = ["—", "—", "—"]

        generate_video(student_id, month, result, highlight, improve_list)
        return str(path), None
    except Exception as exc:  # noqa: BLE001 — gom lỗi để báo trong batch
        return str(path), f"{type(exc).__name__}: {exc}"

